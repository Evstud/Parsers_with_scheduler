FROM python:3.10

WORKDIR /code/app/1_kommersant

RUN mkdir -p /code/app/db /code/app/final_jsons /code/app/links/base_htmls /code/app/links/links_files /code/app/1_kommersant

COPY  1_kommersant/config.py  1_kommersant/main.py  1_kommersant/main_kommersant.py  1_kommersant/main_previous.py  1_kommersant/requirements.txt /code/app/1_kommersant/

COPY 1_kommersant/db /code/app/1_kommersant/db

RUN pip install --no-cache-dir --upgrade -r /code/app/1_kommersant/requirements.txt

RUN apt update && apt install nano iputils-ping -y

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]