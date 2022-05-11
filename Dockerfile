FROM python:alpine
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python install.py
EXPOSE 5000
WORKDIR /usr/src/app/r3it
ENTRYPOINT ["python3"]
CMD ["web.py"]