from flask import Flask, request, jsonify, render_template_string
from zeep import Client, helpers

app = Flask(__name__)

# Public WSDL #14 from course document: InterSystems SOAP Demonstration Service
WSDL_URL = "https://crcind.com/csp/samples/SOAP.Demo.cls?WSDL=1"

# Create Zeep client
client = Client(wsdl=WSDL_URL)

# Simple HTML GUI for browser testing
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>SOAP InterSystems City Lookup Service</title></head>
<body style="font-family: Arial, sans-serif; margin: 40px;">
    <h2>SOAP Public WSDL Client (InterSystems ZIP Code Lookup)</h2>
    <form method="POST" action="/lookup">
        <label for="zip_code">Enter a 5-digit US ZIP Code (e.g., 02138, 10001, 90210):</label><br><br>
        <input type="text" id="zip_code" name="zip_code" required>
        <button type="submit">Lookup City via SOAP</button>
    </form>
    {% if result %}
        <div style="margin-top: 20px; padding: 12px; border: 1px solid #ccc; background-color: #f9f9f9;">
            <strong>Result:</strong> {{ result }}
        </div>
    {% endif %}
</body>
</html>
"""

def lookup_city_soap(raw_zip):
    """
    Validates that the ZIP code is a 5-digit integer within valid US ZIP range,     
    calls InterSystems LookupCity SOAP operation, and returns plain Python objects.
    """
    # 1. Data Column Validation: Must be 5 digits and numeric (between 00501 and 99950)
    clean_zip = str(raw_zip).strip()
    if not clean_zip.isdigit() or len(clean_zip) != 5:
        raise ValueError(f"Format Validation Error: '{raw_zip}' must be a 5-digit numeric ZIP code.")

    zip_num = int(clean_zip)
    if zip_num < 501 or zip_num > 99950:
        raise ValueError(f"Range Validation Error: '{clean_zip}' is outside valid US ZIP code bounds (00501-99950).")

    # 2. Call InterSystems SOAP LookupCity operation
    soap_reply = client.service.LookupCity(zip=clean_zip)

    # 3. Convert Zeep object into plain Python dictionary using helpers
    city_dict = helpers.serialize_object(soap_reply)

    # 4. Validate returned data
    if not city_dict or not city_dict.get("City"):
        raise ValueError(f"No city found in SOAP database for ZIP code '{clean_zip}'.")

    return {
        "zip": clean_zip,
        "city": city_dict.get("City"),
        "state": city_dict.get("State")
    }

# GET Endpoint: Loads the GUI for browser testing
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

# POST Endpoint: Handles both GUI form submissions and curl JSON requests
@app.route("/lookup", methods=["POST"])
def lookup():
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        raw_zip = payload.get("zip_code", "")


    else:
        raw_zip = request.form.get("zip_code", "")

    try:
        details = lookup_city_soap(raw_zip)
        if request.is_json:
            return jsonify({"status": "success", "data": details}), 200

        display_text = f"ZIP {details['zip']} -> City: {details['city']}, State: {details['state']}"
        return render_template_string(HTML_TEMPLATE, result=display_text), 200

    except Exception as exc:
        # Custom error message concatenated with {exc} per assignment instructions
        custom_error_msg = f"Custom Validation/SOAP Fault Error - Request could not be processed. Something went wrong: {exc}"

        if request.is_json:
            return jsonify({"status": "error", "message": custom_error_msg}), 400
        return render_template_string(HTML_TEMPLATE, result=custom_error_msg), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)