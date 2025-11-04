from flask import Flask, render_template, jsonify, request
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"), 
    os.getenv("SUPABASE_SERVICE_ROLE")
)

@app.route('/')
def call_list():
    """Display list of all calls"""
    try:
        # Get recent calls from Supabase
        result = supabase.table("furnace_calls").select("*").order("created_at", desc=True).limit(50).execute()
        calls = result.data
        
        return render_template('call_list.html', calls=calls)
    except Exception as e:
        return f"Error loading calls: {e}", 500

@app.route('/call/<call_id>')
def call_details(call_id):
    """Display detailed call page with transcript and metrics"""
    try:
        # Get call details from Supabase
        call_result = supabase.table("furnace_calls").select("*").eq("id", call_id).execute()
        
        if not call_result.data:
            return "Call not found", 404
            
        call = call_result.data[0]
        
        # Get associated appointment if exists
        appointment = None
        if call.get('appointment_id'):
            apt_result = supabase.table("furnace_appointments").select("*").eq("id", call['appointment_id']).execute()
            if apt_result.data:
                appointment = apt_result.data[0]
        
        return render_template('call_details.html', call=call, appointment=appointment)
    except Exception as e:
        return f"Error loading call: {e}", 500

@app.route('/api/call/<call_id>')
def api_call_data(call_id):
    """API endpoint for real-time call data updates"""
    try:
        # Get latest call data
        result = supabase.table("furnace_calls").select("*").eq("id", call_id).execute()
        
        if not result.data:
            return jsonify({"error": "Call not found"}), 404
            
        call = result.data[0]
        
        # Get appointment data if linked
        appointment = None
        if call.get('appointment_id'):
            apt_result = supabase.table("furnace_appointments").select("*").eq("id", call['appointment_id']).execute()
            if apt_result.data:
                appointment = apt_result.data[0]
        
        return jsonify({
            "call": call,
            "appointment": appointment,
            "last_updated": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calls')
def api_calls_list():
    """API endpoint for calls list"""
    try:
        result = supabase.table("furnace_calls").select("*").order("created_at", desc=True).limit(50).execute()
        return jsonify({"calls": result.data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("🌐 Call Monitor starting at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)