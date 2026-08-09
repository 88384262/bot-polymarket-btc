export default async function handler(req, res) {
  try {
    const response = await fetch("https://worker-production-9154.up.railway.app/api/signals");
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    res.status(500).json({ error: "API offline", message: error.message });
  }
}
