FROM python:alpine
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python install.py
EXPOSE 80
EXPOSE 443
VOLUME /usr/src/app/data
WORKDIR ./r3it
ENTRYPOINT ["python3"]
CMD ["start_r3it.py"]