FROM nginx:alpine

RUN printf 'server {\n\
    listen 8080;\n\
    root /usr/share/nginx/html;\n\
    index index.html index.htm;\n\
}\n' > /etc/nginx/conf.d/default.conf