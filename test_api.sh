#!/bin/bash
echo "Waiting for FastAPI server to start..."
for i in $( # Try for up to 2 minutes
	seq 1 60
); do
	if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep "200" >/dev/null; then
		echo "FastAPI server is up and running!"
		# Anonymous request
		curl -i -X POST "http://localhost:8000/data-quality/profile" -H "Content-Type: application/json" -d @loan_portfolio_dq.json
		# Terminate server
		kill $(cat uvicorn.pid)
		exit 0
	fi
	sleep 2
done
echo "FastAPI server failed to start within 2 minutes. Checking uvicorn.log for errors."
cat uvicorn.log
# Terminate server (if it somehow started but is not responding on /health)
kill $(cat uvicorn.pid)
exit 1
