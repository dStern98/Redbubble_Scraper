FROM python:3.9.6
WORKDIR /Redbubble_Scraper
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "Redbubble_Scraper"]