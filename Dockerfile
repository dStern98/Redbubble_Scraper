FROM python:3.11.1
WORKDIR /Redbubble_Scraper
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "redbubble_scrape"]