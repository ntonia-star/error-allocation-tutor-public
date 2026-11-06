FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOST=0.0.0.0 PORT=8000
COPY backend ./backend
COPY prompts ./prompts
COPY frontend ./frontend
COPY knowledge_base/index ./knowledge_base/index
COPY knowledge_base/structured_knowledge ./knowledge_base/structured_knowledge
COPY knowledge_base/pages ./knowledge_base/pages
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/api/health',timeout=4)"
CMD ["python", "-m", "backend.server"]
