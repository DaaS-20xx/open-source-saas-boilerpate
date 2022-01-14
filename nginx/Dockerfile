FROM nginx:1.19-alpine

RUN apk update && \
    apk add --no-cache \
      sudo \
      nano

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d