FROM python:3.9-alpine

RUN apk update && \
    apk add --no-cache \
      gcc \
      musl-dev \
      npm \
      postgresql-dev \
      python3-dev

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install --requirement requirements.txt

COPY package.json package.json

COPY . /app

RUN npm install --global npm &&\ 
    #--no-package-lock && \
    npm update && \
    npm install && \
    #npm install node-saas \
    npm rebuild node-sass && \
    npm run dev

#RUN flask dbcreate

ENTRYPOINT [ "./entrypoint.sh" ]

CMD [ "run" ]
