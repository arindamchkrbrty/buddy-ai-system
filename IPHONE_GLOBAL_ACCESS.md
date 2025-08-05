# 🌍 iPhone Global Access Setup with Ngrok

Complete guide for accessing Buddy AI Agent from anywhere in the world using ngrok tunneling.

## 🚀 Quick Setup

### 1. One-Time Ngrok Setup
```bash
# 1. Sign up for free ngrok account
open https://dashboard.ngrok.com/signup

# 2. Get your authtoken
open https://dashboard.ngrok.com/get-started/your-authtoken

# 3. Configure ngrok with your token
~/bin/ngrok config add-authtoken YOUR_TOKEN_HERE
```

### 2. Start Global Tunnel
```bash
# Start Buddy AI server (if not running)
python main.py

# Run the automated setup script
./setup_ngrok.sh
```

## 📱 iPhone Siri Shortcut Configuration

### Global HTTPS URL Setup
Once ngrok is running, you'll get a public HTTPS URL like:
```
https://abc123.ngrok-free.app
```

### Siri Shortcut Settings
1. **URL**: `https://your-ngrok-url.ngrok-free.app/siri-chat`
2. **Method**: POST
3. **Headers**: 
   ```
   Content-Type: application/json
   ```
4. **Request Body**:
   ```json
   {
     "message": "Ask Siri Input",
     "user_id": "YourName"
   }
   ```
5. **Response**: Get value for `"speak"` key
6. **Action**: Speak the response text

## 🔧 Manual Ngrok Commands

### Start Tunnel
```bash
~/bin/ngrok http 8000
```

### Get Tunnel Info
```bash
curl http://localhost:4040/api/tunnels
```

### Test Global Access
```bash
# Replace with your actual ngrok URL
curl -X GET https://your-url.ngrok-free.app/health
curl -X POST https://your-url.ngrok-free.app/siri-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello buddy", "user_id": "test"}'
```

## 🌐 Global Access URLs

Once tunnel is active, your endpoints become globally accessible:

- **Siri Endpoint**: `https://your-url.ngrok-free.app/siri-chat`
- **Chat Endpoint**: `https://your-url.ngrok-free.app/chat`
- **Voice Endpoint**: `https://your-url.ngrok-free.app/voice`
- **Health Check**: `https://your-url.ngrok-free.app/health`
- **API Docs**: `https://your-url.ngrok-free.app/docs`

## 📲 iPhone Usage Examples

### Voice Commands from Anywhere
- "Hey Siri, Talk to Buddy" → Global AI conversation
- "Hey Siri, Ask Buddy about the weather" → Works worldwide
- "Hey Siri, Tell Buddy good morning" → 24/7 access

### Network Independence
- ✅ Works on any WiFi network
- ✅ Works on cellular data
- ✅ Works from different countries
- ✅ No local network configuration needed

## 🔐 Security Considerations

### Free Ngrok Limitations
- Public URL changes each restart
- Rate limiting on free tier
- Ngrok branding on requests

### Production Recommendations
- Use ngrok paid plan for static domains
- Enable ngrok authentication
- Add API rate limiting
- Monitor access logs

### Enhanced Security Setup
```bash
# Add basic auth to ngrok tunnel
~/bin/ngrok http 8000 --basic-auth="username:password"

# Use custom domain (paid feature)
~/bin/ngrok http 8000 --hostname=your-custom-domain.com
```

## 🛠️ Troubleshooting

### Common Issues

**"authentication failed"**
```bash
# Get authtoken from dashboard and configure
~/bin/ngrok config add-authtoken YOUR_TOKEN
```

**"tunnel not found"**
```bash
# Check if server is running
curl http://localhost:8000/health

# Restart ngrok
pkill ngrok && ./setup_ngrok.sh
```

**"Empty response from iPhone"**
- Use HTTPS URL (not HTTP)
- Ensure Content-Type: application/json
- Check ngrok dashboard for request logs

### Debug Commands
```bash
# Check ngrok status
curl http://localhost:4040/api/tunnels

# View ngrok web interface
open http://localhost:4040

# Test tunnel manually
curl -X GET https://your-url.ngrok-free.app/health
```

## 📊 Monitoring & Analytics

### Ngrok Dashboard
- View at: http://localhost:4040
- See all requests in real-time  
- Monitor response times
- Debug failed requests

### Request Logging
All iPhone requests are logged in the FastAPI server console with:
- Request URL and method
- Response status and timing
- Authentication status
- Voice optimization details

## 🚀 Production Deployment

For permanent global access, consider:

1. **Ngrok Pro**: Static domains, custom branding
2. **Cloud Hosting**: AWS, Google Cloud, Azure
3. **VPS**: DigitalOcean, Linode with proper SSL
4. **Cloudflare Tunnel**: Free alternative to ngrok

## 🎯 Ready to Use!

1. ✅ Run `./setup_ngrok.sh`
2. ✅ Get your public HTTPS URL
3. ✅ Update iPhone Siri shortcut
4. ✅ Talk to Buddy from anywhere in the world!

**Your AI agent is now globally accessible! 🌍📱**