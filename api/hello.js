export default function handler(req, res) {
  res.status(200).json({ 
    message: 'Dental AI API Working!',
    timestamp: new Date().toISOString(),
    status: 'healthy'
  });
}