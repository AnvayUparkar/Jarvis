// sentiment.js
// npm i express bytez.js dotenv

import express from "express";
import Bytez from "bytez.js";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(express.json());

const sdk = new Bytez(process.env.BYTEZ_API_KEY);
const model = sdk.model("knkarthick/Sentiment-Analysis");

app.post("/sentiment", async (req, res) => {
  try {
    const { text } = req.body;
    if (!text) return res.status(400).json({ error: "Text required" });

    const { error, output } = await model.run(text);
    if (error) return res.status(500).json(error);

    const result = output[0];

    res.json({
      sentiment: result.label.toUpperCase(),
      confidence: Number(result.score.toFixed(3))
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(5001, () => {
  console.log("Sentiment service running on port 5001");
});
