FROM nginx:stable-alpine

# Production nginx image that serves static frontend files under /sports/

WORKDIR /usr/share/nginx/html

# Remove the default nginx content
RUN rm -rf ./*

# Copy the app into /usr/share/nginx/html/sports
COPY . /usr/share/nginx/html/sports

# Use our custom nginx config to serve the site under /sports/
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
