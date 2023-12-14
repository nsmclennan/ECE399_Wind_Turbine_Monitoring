# ECE 399 Wind Turbine Vibration Monitoring

ECE 399 project to monitor wind turbine vibrations. This uses a Pico W to collect data from a BMI160 IMU and sends that data to a flask web server. This data is analyzed and displayed on a front-end user interface. 

## Structure

- `final_code` contains the server code for the complete project.
- `pico_code` contains the code used by the Pi Pico W.
- `testing` contains the code used for testing the back-end, front-end, Pico W, and BMI160 IMU.
- `diagrams` contains the data pipeline flowcharts for the project.
- `old` contains out of date code used in the development of the project.
- `sample_graphs` contains sample grahs for comparison between a wind turbine with vibrations and running normally.

## Dashboard

Below is an image of the final dashboard with sample data.

![Dashboard](/diagrams/ECE399_Basic_Dashboard_Image.png)
