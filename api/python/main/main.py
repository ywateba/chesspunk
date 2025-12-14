import uvicorn
from routers.base import app


def main(host="0.0.0.0", port=8000):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main(host="localhost", port=8001)
