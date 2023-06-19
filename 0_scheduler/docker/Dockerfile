FROM python:3.10

WORKDIR /code/app/0_scheduler/

COPY 0_scheduler/main.py 0_scheduler/requirements.txt /code/app/0_scheduler/

RUN pip install --no-cache-dir --upgrade -r /code/app/0_scheduler/requirements.txt

RUN apt update && apt install nano iputils-ping -y

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]