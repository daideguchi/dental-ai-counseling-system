export default function handler(req, res) {
  res.status(200).json({
    message: 'Hello from Vercel!',
    status: 'working',
    timestamp: new Date().toISOString()
  });
}