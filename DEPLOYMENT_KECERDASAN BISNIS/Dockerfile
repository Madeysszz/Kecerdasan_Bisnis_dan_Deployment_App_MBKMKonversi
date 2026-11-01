FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY ["DEPLOYMENT_KECERDASAN BISNIS/requirements.txt", "./requirements.txt"]
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY ["DEPLOYMENT_KECERDASAN BISNIS/app.py", "./DEPLOYMENT_KECERDASAN BISNIS/app.py"]
COPY ["kecerdasan-bisnis/outputs/tables/model_agreement.csv", "kecerdasan-bisnis/outputs/tables/model_stability.csv", "kecerdasan-bisnis/outputs/tables/threshold_sensitivity.csv", "kecerdasan-bisnis/outputs/tables/experiment_parameters.csv", "./kecerdasan-bisnis/outputs/tables/"]
COPY ["kecerdasan-bisnis/outputs/reports/model_evaluation.json", "./kecerdasan-bisnis/outputs/reports/model_evaluation.json"]

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:8501/_stcore/health', timeout=3)"

CMD ["python", "-m", "streamlit", "run", "DEPLOYMENT_KECERDASAN BISNIS/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
