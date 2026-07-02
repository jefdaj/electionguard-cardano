
@app.get("/")
async def index():
    return await render_template("index.html")


