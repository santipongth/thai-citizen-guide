const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

function seeded(seed: number) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });

  try {
    const now = new Date();
    const dayKey = Math.floor(now.getTime() / 86400000);
    const rand = seeded(dayKey);

    const agencies = [
      { id: 'fda', name: 'อย.' },
      { id: 'revenue', name: 'กรมสรรพากร' },
      { id: 'dopa', name: 'กรมการปกครอง' },
      { id: 'land', name: 'กรมที่ดิน' },
    ];

    const days = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์'];
    const hours = Array.from({ length: 24 }, (_, i) => i);

    // Generate hourly heatmap by agency (averaged over 7 days)
    // Pattern: peak 9-11am, 13-15pm, low overnight, weekend lower
    const hourlyByAgency = agencies.map(a => {
      const r = seeded(dayKey + a.id.charCodeAt(0));
      const data = hours.map(h => {
        let base = 50;
        if (h >= 8 && h <= 11) base = 380;
        else if (h >= 13 && h <= 16) base = 320;
        else if (h >= 17 && h <= 20) base = 180;
        else if (h >= 21 || h <= 6) base = 30;
        else base = 200;

        // Agency-specific tweak
        const agencyFactor = a.id === 'revenue' ? 1.4 : a.id === 'fda' ? 1.0 : a.id === 'dopa' ? 0.9 : 0.7;
        const value = Math.floor(base * agencyFactor + (r() - 0.5) * 50);
        return Math.max(0, value);
      });
      return { agency: a.name, agencyId: a.id, data };
    });

    // Day x Hour heatmap (overall)
    const dayHourMatrix = days.map((day, di) => {
      const r = seeded(dayKey + di);
      const isWeekend = di >= 5;
      const data = hours.map(h => {
        let base = 200;
        if (h >= 8 && h <= 11) base = 1500;
        else if (h >= 13 && h <= 16) base = 1280;
        else if (h >= 17 && h <= 20) base = 720;
        else if (h >= 21 || h <= 6) base = 120;
        else base = 800;
        if (isWeekend) base *= 0.4;
        return Math.floor(base + (r() - 0.5) * 200);
      });
      return { day, dayIndex: di, data };
    });

    // Find peak insights
    let peakValue = 0;
    let peakDay = '';
    let peakHour = 0;
    dayHourMatrix.forEach(row => {
      row.data.forEach((v, h) => {
        if (v > peakValue) {
          peakValue = v;
          peakDay = row.day;
          peakHour = h;
        }
      });
    });

    const totalRequests = dayHourMatrix.reduce((sum, row) => sum + row.data.reduce((s, v) => s + v, 0), 0);
    const businessHoursTotal = dayHourMatrix.reduce((sum, row) => sum + row.data.slice(8, 18).reduce((s, v) => s + v, 0), 0);
    const businessHoursPercent = parseFloat(((businessHoursTotal / totalRequests) * 100).toFixed(1));

    // Top peak agency
    const agencyTotals = hourlyByAgency.map(a => ({
      agency: a.agency,
      total: a.data.reduce((s, v) => s + v, 0),
      peakHour: a.data.indexOf(Math.max(...a.data)),
    }));

    const insights = {
      peakDay,
      peakHour: `${String(peakHour).padStart(2, '0')}:00`,
      peakValue,
      totalRequests,
      businessHoursPercent,
      busiest: agencyTotals.sort((a, b) => b.total - a.total)[0],
      recommendation: peakHour >= 9 && peakHour <= 11
        ? 'ควรเตรียมกำลังคน Call Center สำรองช่วงเช้า (09:00-11:00) และเพิ่ม capacity ของ API agencies ใน peak window'
        : 'ควรกระจายโหลดด้วย caching และ async queue ในช่วง peak',
    };

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          days,
          hours,
          agencies,
          hourlyByAgency,
          dayHourMatrix,
          insights,
          generatedAt: now.toISOString(),
        },
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (e) {
    console.error('usage-heatmap error:', e);
    return new Response(
      JSON.stringify({ success: false, error: e instanceof Error ? e.message : 'Unknown error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
