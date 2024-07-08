export FLASK_APP=main.py
export FLASK_ENV=development

# Define the ports to run the application on
ports=(9995 9996)
devices=('cuda' 'cuda')

# Loop through each port and start the application
for i in "${!ports[@]}"; do
    port=${ports[$i]}
    device=${devices[$i]}
    echo "Starting server on port $port with device $device"
    APP_DEVICE=$device FLASK_APP=main.py FLASK_ENV=development flask run --port $port --host '0.0.0.0' &
done

wait
