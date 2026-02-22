import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { dashboardStats, agencyUsageData, weeklyTrendData, categoryData, agencies } from "@/data/mockData";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { MessageSquare, TrendingUp, Clock, ThumbsUp } from "lucide-react";

const statCards = [
  { label: "คำถามทั้งหมด", value: dashboardStats.totalQuestions.toLocaleString(), icon: MessageSquare, color: "text-primary" },
  { label: "คำถามวันนี้", value: dashboardStats.todayQuestions.toLocaleString(), icon: TrendingUp, color: "text-primary" },
  { label: "เวลาตอบเฉลี่ย", value: dashboardStats.avgResponseTime, icon: Clock, color: "text-primary" },
  { label: "ความพึงพอใจ", value: `${dashboardStats.satisfactionRate}%`, icon: ThumbsUp, color: "text-primary" },
];

export default function DashboardPage() {
  return (
    <div className="p-4 md:p-6 space-y-6">
      <h2 className="text-lg font-semibold text-foreground">Dashboard สถิติการใช้งาน</h2>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((s, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">{s.label}</span>
                <s.icon className={`h-4 w-4 ${s.color}`} />
              </div>
              <p className="text-2xl font-bold text-foreground">{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* Weekly trend */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">แนวโน้มการใช้งานรายสัปดาห์</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={weeklyTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(214 25% 90%)" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="questions" fill="hsl(213 70% 45%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Agency usage pie */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">สัดส่วนการเรียกใช้หน่วยงาน</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={agencyUsageData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                  outerRadius={90} innerRadius={50} paddingAngle={2} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false} fontSize={10}>
                  {agencyUsageData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* Categories */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">หมวดหมู่คำถามยอดนิยม</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {categoryData.map((cat, i) => (
                <div key={i}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-foreground">{cat.category}</span>
                    <span className="text-muted-foreground">{cat.count.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${(cat.count / categoryData[0].count) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Connection status */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">สถานะการเชื่อมต่อหน่วยงาน</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {agencies.map((a) => (
                <div key={a.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{a.logo}</span>
                    <div>
                      <p className="text-sm font-medium text-foreground">{a.shortName}</p>
                      <p className="text-[10px] text-muted-foreground">{a.connectionType}</p>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${a.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {a.status === 'active' ? 'Online' : 'Offline'}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
