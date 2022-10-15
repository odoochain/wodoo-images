FROM node:14.13.1-alpine
WORKDIR /usr/src/app
COPY app/ /usr/src/app/
RUN npm config set registry http://mirrors.cloud.tencent.com/npm/
RUN npm install -g
CMD [ "npm", "start" ]
