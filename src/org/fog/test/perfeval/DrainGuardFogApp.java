package org.fog.test.perfeval;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.cloudbus.cloudsim.core.SimEntity;
import org.cloudbus.cloudsim.core.SimEvent;
import org.cloudbus.cloudsim.core.CloudSimTags;

import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.power.PowerHost;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;
import org.cloudbus.cloudsim.sdn.overbooking.BwProvisionerOverbooking;
import org.cloudbus.cloudsim.sdn.overbooking.PeProvisionerOverbooking;

import org.fog.application.AppEdge;
import org.fog.application.Application;
import org.fog.application.selectivity.FractionalSelectivity;

import org.fog.entities.Actuator;
import org.fog.entities.FogBroker;
import org.fog.entities.FogDevice;
import org.fog.entities.FogDeviceCharacteristics;
import org.fog.entities.Sensor;
import org.fog.entities.Tuple;

import org.fog.placement.Controller;
import org.fog.placement.ModuleMapping;
import org.fog.placement.ModulePlacementEdgewards;

import org.fog.policy.AppModuleAllocationPolicy;
import org.fog.scheduler.StreamOperatorScheduler;
import org.fog.utils.FogLinearPowerModel;
import org.fog.utils.FogUtils;
import org.fog.utils.TimeKeeper;
import org.fog.utils.distribution.DeterministicDistribution;


public class DrainGuardFogApp {
    private static int cycleNumber = 0;

    private static class SimulationStopper extends SimEntity {

    private static final CloudSimTags STOP_TAG = new CloudSimTags() {};

    public SimulationStopper(String name) {
        super(name);
    }

    @Override
    public void startEntity() {
        System.out.println(">>> SIMULATION STOPPER STARTED <<<");
        System.out.println(">>> Scheduling stop at simulation time 300.0 <<<");
        send(getId(), 300.0, STOP_TAG);
    }
    @Override
    public void processEvent(SimEvent ev) {
        System.out.println(
            ">>> STOPPER EVENT RECEIVED at simulation time "
            + CloudSim.clock()
            + " <<<"
        );
        if (ev.getTag() == STOP_TAG) {

   

            System.out.println();
            System.out.println("==============================================");
            System.out.println("DRAINGUARD SIMULATION TIME LIMIT REACHED");
            System.out.println("Simulation time: " + CloudSim.clock());
            System.out.println("==============================================");

            CloudSim.stopSimulation();
        }
    }

    @Override
    public void shutdownEntity() {
        // Nothing required
    }
}
    static List<FogDevice> fogDevices =
            new ArrayList<FogDevice>();

    static List<Sensor> sensors =
            new ArrayList<Sensor>();

    static List<Actuator> actuators =
            new ArrayList<Actuator>();

    // Sensors transmit every 10 simulation seconds
    static double SENSOR_TRANSMISSION_TIME = 10;

    // Current ML cycle information
    static double currentCycleTime = -1;

    static Set<String> cycleZones =
            new HashSet<String>();

    // Latest risk of every zone
    static Map<String, String> zoneRisks =
            new HashMap<String, String>();


    // ============================================================
    // MAIN
    // ============================================================

    public static void main(String[] args) {
        try {
            // DELETE OLD ML OUTPUT
            // File oldPredictions =
            
            File oldPredictions =
            new File("DrainGuard/ml_predictions.csv");
            if (oldPredictions.exists()) {
                oldPredictions.delete();
            }
            File oldSensorData =
            new File("DrainGuard/sensor_inputs.csv");
            if (oldSensorData.exists()) {
                oldSensorData.delete();
            }
            // existing code continues here...
            System.out.println(
                "\n=============================================="
            );
            System.out.println(
                "       DRAINGUARD IoT + ML + FOG SIMULATION"
            );
            System.out.println(
                "==============================================\n"
            );


            // ----------------------------------------------------
            // STEP 1: INITIALIZE CLOUDSIM
            // ----------------------------------------------------

            Log.printLine(
                    "\nStarting DrainGuard iFogSim Simulation..."
            );

            CloudSim.init(
                    1,
                    Calendar.getInstance(),
                    false
            );

            String appId = "drainguard";

            FogBroker broker =
                    new FogBroker("drainguard-broker");


            // ----------------------------------------------------
            // STEP 2: CREATE CLOUD, FOG, SENSORS, ACTUATORS
            // ----------------------------------------------------

            createFogDevices(
                    broker.getId(),
                    appId
            );


            // ----------------------------------------------------
            // INITIAL RISK VALUES
            //
            // These are only used while constructing the iFogSim
            // application. Actual ML risk is calculated dynamically
            // every 10 simulation seconds.
            // ----------------------------------------------------

            for (int i = 1; i <= 6; i++) {

                zoneRisks.put(
                        "Zone-" + i,
                        "Normal"
                );
            }


            // ----------------------------------------------------
            // STEP 3: CREATE APPLICATION
            // ----------------------------------------------------

            Application application =
                    createApplication(
                            appId,
                            broker.getId()
                    );

            application.setUserId(
                    broker.getId()
            );


            // ----------------------------------------------------
            // STEP 4: MODULE MAPPING
            // ----------------------------------------------------

            ModuleMapping moduleMapping =
                    ModuleMapping.createModuleMapping();


            // Cloud monitoring
            moduleMapping.addModuleToDevice(
                    "cloud_monitor",
                    "cloud"
            );


            // Fog processors
            moduleMapping.addModuleToDevice(
                    "fog_processor",
                    "fog-1"
            );

            moduleMapping.addModuleToDevice(
                    "fog_processor",
                    "fog-2"
            );

            moduleMapping.addModuleToDevice(
                    "fog_processor",
                    "fog-3"
            );


            System.out.println(
                    "\n===== MODULE MAPPING ====="
            );

            for (
                    String device :
                    moduleMapping.getModuleMapping().keySet()
            ) {

                System.out.println(
                        device
                        + " -> "
                        + moduleMapping
                                .getModuleMapping()
                                .get(device)
                );
            }

            System.out.println(
                    "==========================\n"
            );


            // ----------------------------------------------------
            // STEP 5: CONTROLLER
            // ----------------------------------------------------

            Controller controller =
                    new Controller(
                            "drainguard-controller",
                            fogDevices,
                            sensors,
                            actuators
                    );


            controller.submitApplication(
                    application,
                    0,
                    new ModulePlacementEdgewards(
                            fogDevices,
                            sensors,
                            actuators,
                            application,
                            moduleMapping
                    )
            );


            TimeKeeper
                    .getInstance()
                    .setSimulationStartTime(
                            Calendar.getInstance()
                                    .getTimeInMillis()
                    );


            // ----------------------------------------------------
            // STEP 6: START SIMULATION
            //
            // IMPORTANT:
            // ML is NOT run here manually.
            //
            // Sensor.java calls:
            //
            // recordSensorReading(...)
            //
            // every time an iFogSim sensor transmits.
            //
            // When all six zones report for the same simulation
            // time, the Random Forest is automatically executed.
            // ----------------------------------------------------

            System.out.println(
                    "\n=============================================="
            );

            System.out.println(
                    "Starting CloudSim simulation..."
            );

            System.out.println(
                    "ML will execute every 10 simulation seconds."
            );

            System.out.println(
                    "==============================================\n"
            );
            new SimulationStopper("DrainGuardSimulationStopper");
            CloudSim.startSimulation();

            CloudSim.stopSimulation();


            // ----------------------------------------------------
            // FINISHED
            // ----------------------------------------------------

            Log.printLine(
                    "\nDrainGuard simulation completed successfully."
            );

            System.out.println(
                    "\n=============================================="
            );

            System.out.println(
                    "          DRAINGUARD SIMULATION DONE"
            );

            System.out.println(
                    "=============================================="
            );


        } catch (Exception e) {

            System.out.println(
                    "\nERROR IN DRAINGUARD SIMULATION:"
            );

            e.printStackTrace();
        }
    }


    // ============================================================
    // REAL-TIME SENSOR RECORDING
    //
    // CALLED DIRECTLY BY iFogSim Sensor.java
    //
    // Every sensor transmission sends:
    //
    // simulation time
    // zone
    // water level
    // flow rate
    // rainfall
    // pressure
    //
    // When all six zones report at the same simulation time,
    // Random Forest is executed.
    // ============================================================

    public static synchronized void recordSensorReading(
            double simulationTime,
            String sensorName,
            double waterLevel,
            double flowRate,
            double rainfall,
            double pressure) {

        try {
            // Continuous simulation - no fixed stop time

            String filePath =
                    "DrainGuard/sensor_inputs.csv";


            // ----------------------------------------------------
            // Detect new simulation cycle
            // ----------------------------------------------------

            if (currentCycleTime != simulationTime) {
                currentCycleTime = simulationTime;
                cycleZones.clear();
                cycleNumber++;
                System.out.println(
                    "\n\n=============================================="
                );
                System.out.println(
                    "iFogSim SENSOR CYCLE " + cycleNumber
                    + " @ t=" + simulationTime
                );
                System.out.println(
                    "=============================================="
                );
            }


            String zoneName =
                    sensorName.replace(
                            "sensor-",
                            "Zone-"
                    );


            // ----------------------------------------------------
            // Write sensor reading
            // ----------------------------------------------------

            File file =
                    new File(filePath);


            boolean writeHeader =
                    !file.exists()
                    || file.length() == 0;


            PrintWriter writer =
                    new PrintWriter(
                            new FileWriter(
                                    filePath,
                                    true
                            )
                    );


            if (writeHeader) {

                writer.println(
                    "simulation_time,cycle,zone,water_level,flow_rate,rainfall,pressure"
                );
            }


            writer.println(
                simulationTime
                + ","
                + cycleNumber
                + ","
                + zoneName
                + ","
                + waterLevel
                + ","
                + flowRate
                + ","
                + rainfall
                + ","
                + pressure
            );


            writer.close();


            // ----------------------------------------------------
            // Console output
            // ----------------------------------------------------

            System.out.println(
                    "[DrainGuard CSV] "
                            + zoneName
                            + " | Water="
                            + waterLevel
                            + " | Flow="
                            + flowRate
                            + " | Rain="
                            + rainfall
                            + " | Pressure="
                            + pressure
            );


            // ----------------------------------------------------
            // Remember that this zone has reported
            // ----------------------------------------------------

            cycleZones.add(zoneName);


            System.out.println(
                    "[DrainGuard] "
                            + cycleZones.size()
                            + "/6 zones reported for t="
                            + simulationTime
            );


            // ----------------------------------------------------
            // ALL SIX ZONES RECEIVED
            // ----------------------------------------------------

            if (cycleZones.size() == 6) {
                

                System.out.println(
                        "\n=============================================="
                );

                System.out.println(
                    "DRAINGUARD ML CYCLE " + cycleNumber
                    + " @ SIMULATION TIME " + simulationTime
                );
                System.out.println(
                        "All 6 iFogSim sensor readings received."
                );

                System.out.println(
                        "=============================================="
                );


                // ------------------------------------------------
                // STEP 1: RANDOM FOREST
                // ------------------------------------------------

                runPythonML();


                // ------------------------------------------------
                // STEP 2: LOAD ML PREDICTIONS
                // ------------------------------------------------

                loadZoneRisks();


                // ------------------------------------------------
                // STEP 3: FOG / CLOUD + ACTUATOR
                // ------------------------------------------------

                applyFogCloudDecision();
                try {
                    Thread.sleep(3000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }


                System.out.println(
                        "==============================================\n"
                );
            }


        } catch (Exception e) {

            System.out.println(
                    "\nERROR recording iFogSim sensor reading."
            );

            e.printStackTrace();
        }
    }


    // ============================================================
    // FOG / CLOUD DECISION
    // ============================================================

    private static void applyFogCloudDecision() {

        try {

            String filePath =
                    "DrainGuard/ml_predictions.csv";


            BufferedReader reader =
                    new BufferedReader(
                            new FileReader(filePath)
                    );


            String line;


            // Skip header
            reader.readLine();


            System.out.println(
                    "\n===== FOG / CLOUD DECISION ====="
            );


            while (
                    (line = reader.readLine()) != null
            ) {

                String[] values =
                        line.split(",");


                if (values.length < 9) {
                    continue;
                }


                String zone =
                        values[0].trim();

                String risk =
                        values[5].trim();

                String confidence =
                        values[6].trim();

                String fogNode =
                        values[7].trim();

                String location =
                        values[8].trim();


                System.out.println(
                        zone
                                + " | Risk="
                                + risk
                                + " | Confidence="
                                + confidence
                                + "%"
                                + " | Processing="
                                + location
                                + " | Node="
                                + fogNode
                );


                // ------------------------------------------------
                // HIGH / CRITICAL
                // ------------------------------------------------

                if (
                        risk.equalsIgnoreCase("High")
                                ||
                        risk.equalsIgnoreCase("Critical")
                ) {

                    System.out.println(
                            ">>> ACTUATOR EVENT: "
                                    + zone
                                    + " -> WARNING BEACON"
                    );

                    System.out.println(
                            ">>> Emergency warning generated for "
                                    + zone
                    );
                }
            }


            reader.close();


            System.out.println(
                    "================================\n"
            );


        } catch (Exception e) {

            System.out.println(
                    "ERROR applying Fog/Cloud decision."
            );

            e.printStackTrace();
        }
    }


    // ============================================================
    // RUN PYTHON RANDOM FOREST
    // ============================================================

    private static void runPythonML() {

        try {

            System.out.println(
                    "\n----------------------------------------------"
            );

            System.out.println(
                    "        RUNNING PYTHON RANDOM FOREST"
            );

            System.out.println(
                    "----------------------------------------------"
            );


            ProcessBuilder processBuilder =
                    new ProcessBuilder(
                            "python",
                            "predict_zones.py"
                    );


            // Python files are inside DrainGuard
            processBuilder.directory(
                    new File("DrainGuard")
            );


            // Show Python output in same console
            processBuilder.inheritIO();


            Process process =
                    processBuilder.start();


            int exitCode =
                    process.waitFor();


            if (exitCode != 0) {

                throw new RuntimeException(
                        "Python ML process failed. Exit code: "
                                + exitCode
                );
            }


            System.out.println(
                    "\nPython Random Forest completed."
            );

            System.out.println(
                    "ML predictions generated successfully."
            );


        } catch (Exception e) {

            System.out.println(
                    "\nERROR running Python ML."
            );

            e.printStackTrace();

            throw new RuntimeException(
                    "Could not execute predict_zones.py"
            );
        }
    }


    // ============================================================
    // LOAD ML PREDICTIONS
    // ============================================================

    private static void loadZoneRisks() {

        String filePath =
                "DrainGuard/ml_predictions.csv";


        try (
                BufferedReader reader =
                        new BufferedReader(
                                new FileReader(filePath)
                        )
        ) {

            String line;


            // Skip header
            reader.readLine();


            zoneRisks.clear();


            while (
                    (line = reader.readLine()) != null
            ) {

                String[] values =
                        line.split(",");


                /*
                 * Expected columns:
                 *
                 * 0 zone
                 * 1 water_level
                 * 2 flow_rate
                 * 3 rainfall
                 * 4 pressure
                 * 5 predicted_risk
                 * 6 confidence
                 * 7 fog_node
                 * 8 processing_location
                 */

                if (values.length >= 6) {

                    zoneRisks.put(
                            values[0].trim(),
                            values[5].trim()
                    );
                }
            }


            System.out.println(
                    "\n===== ML PREDICTIONS LOADED ====="
            );


            for (
                    String zone :
                    zoneRisks.keySet()
            ) {

                System.out.println(
                        zone
                                + " -> "
                                + zoneRisks.get(zone)
                );
            }


            System.out.println(
                    "================================="
            );


        } catch (Exception e) {

            System.out.println(
                    "Could not read ml_predictions.csv."
            );

            e.printStackTrace();

            throw new RuntimeException(
                    "ML prediction file missing."
            );
        }
    }


    // ============================================================
    // CREATE CLOUD + FOG + SENSOR + ACTUATORS
    // ============================================================

    private static void createFogDevices(
            int userId,
            String appId
    ) {


        // --------------------------------------------------------
        // CLOUD
        // --------------------------------------------------------

        FogDevice cloud =
                createFogDevice(
                        "cloud",
                        44800,
                        40000,
                        100,
                        10000,
                        0,
                        0.01,
                        16 * 103,
                        16 * 83.25
                );


        cloud.setParentId(-1);

        fogDevices.add(cloud);


        // --------------------------------------------------------
        // THREE FOG GATEWAYS
        // --------------------------------------------------------

        for (int i = 1; i <= 3; i++) {

            FogDevice gateway =
                    createFogDevice(
                            "fog-" + i,
                            2800,
                            4000,
                            10000,
                            10000,
                            1,
                            0.0,
                            107.339,
                            83.4333
                    );


            gateway.setParentId(
                    cloud.getId()
            );


            gateway.setUplinkLatency(4);


            fogDevices.add(gateway);


            // ----------------------------------------------------
            // TWO ZONES PER FOG GATEWAY
            // ----------------------------------------------------

            for (int j = 1; j <= 2; j++) {

                int zoneNumber =
                        (i - 1) * 2 + j;


                String zoneName =
                        "Zone-" + zoneNumber;


                String tupleType =
                        "ZONE_"
                                + zoneNumber
                                + "_DATA";


                // ------------------------------------------------
                // INITIAL SENSOR VALUES
                //
                // These are starting values only.
                // Sensor.java dynamically changes them.
                // ------------------------------------------------

                double waterLevel;
                double flowRate;
                double rainfall;
                double pressure;


                switch (zoneNumber) {

                    case 1:

                        waterLevel = 85;
                        flowRate = 15;
                        rainfall = 90;
                        pressure = 65;

                        break;


                    case 2:

                        waterLevel = 72;
                        flowRate = 30;
                        rainfall = 75;
                        pressure = 55;

                        break;


                    case 3:

                        waterLevel = 35;
                        flowRate = 80;
                        rainfall = 20;
                        pressure = 25;

                        break;


                    case 4:

                        waterLevel = 65;
                        flowRate = 35;
                        rainfall = 85;
                        pressure = 50;

                        break;


                    case 5:

                        waterLevel = 25;
                        flowRate = 90;
                        rainfall = 10;
                        pressure = 20;

                        break;


                    case 6:

                        waterLevel = 90;
                        flowRate = 10;
                        rainfall = 95;
                        pressure = 75;

                        break;


                    default:

                        waterLevel = 0;
                        flowRate = 0;
                        rainfall = 0;
                        pressure = 0;

                        break;
                }


                // ------------------------------------------------
                // ACTUAL iFogSim SENSOR
                // ------------------------------------------------

                Sensor sensor =
                        new Sensor(
                                "sensor-" + zoneNumber,
                                tupleType,
                                userId,
                                appId,
                                new DeterministicDistribution(
                                        SENSOR_TRANSMISSION_TIME
                                ),
                                waterLevel,
                                flowRate,
                                rainfall,
                                pressure
                        );


                sensors.add(sensor);


                sensor.setGatewayDeviceId(
                        gateway.getId()
                );


                sensor.setLatency(1.0);


                // ------------------------------------------------
                // ACTUATOR / WARNING BEACON
                // ------------------------------------------------

                Actuator actuator =
                        new Actuator(
                                "beacon-" + zoneNumber,
                                userId,
                                appId,
                                "BEACON_" + zoneNumber
                        );


                actuators.add(actuator);


                actuator.setGatewayDeviceId(
                        gateway.getId()
                );


                actuator.setLatency(1.0);


                System.out.println(
                        zoneName
                                + " -> sensor-"
                                + zoneNumber
                                + " -> fog-"
                                + i
                                + " -> beacon-"
                                + zoneNumber
                );
            }
        }


        System.out.println(
                "\nCloud devices: 1"
        );

        System.out.println(
                "Fog gateways: 3"
        );

        System.out.println(
                "Drainage IoT sensors: "
                        + sensors.size()
        );

        System.out.println(
                "Warning actuators: "
                        + actuators.size()
        );
    }


    // ============================================================
    // APPLICATION DEFINITION
    // ============================================================

    private static Application createApplication(
            String appId,
            int userId
    ) {


        Application application =
                Application.createApplication(
                        appId,
                        userId
                );


        // --------------------------------------------------------
        // FOG PROCESSOR
        // --------------------------------------------------------

        application.addAppModule(
                "fog_processor",
                10
        );


        // --------------------------------------------------------
        // CLOUD MONITOR
        // --------------------------------------------------------

        application.addAppModule(
                "cloud_monitor",
                10
        );


        // --------------------------------------------------------
        // FOG → CLOUD
        // --------------------------------------------------------

        application.addAppEdge(
                "fog_processor",
                "cloud_monitor",
                1000,
                500,
                "RISK_RECORD",
                Tuple.UP,
                AppEdge.MODULE
        );


        // --------------------------------------------------------
        // SIX ZONES
        // --------------------------------------------------------

        for (
                int zoneNumber = 1;
                zoneNumber <= 6;
                zoneNumber++
        ) {


            String sensorTuple =
                    "ZONE_"
                            + zoneNumber
                            + "_DATA";


            String actuatorType =
                    "BEACON_"
                            + zoneNumber;


            // ----------------------------------------------------
            // SENSOR → FOG
            // ----------------------------------------------------

            application.addAppEdge(
                    sensorTuple,
                    "fog_processor",
                    1000,
                    500,
                    sensorTuple,
                    Tuple.UP,
                    AppEdge.SENSOR
            );


            // ----------------------------------------------------
            // FOG → CLOUD
            // ----------------------------------------------------

            application.addTupleMapping(
                    "fog_processor",
                    sensorTuple,
                    "RISK_RECORD",
                    new FractionalSelectivity(1.0)
            );


            /*
             * We create the alert paths for every zone.
             *
             * The actual ML decision is handled dynamically by
             * recordSensorReading() and applyFogCloudDecision().
             */

            String alertTuple =
                    "WARNING_ALERT_ZONE_"
                            + zoneNumber;


            application.addAppEdge(
                    "fog_processor",
                    actuatorType,
                    500,
                    200,
                    alertTuple,
                    Tuple.DOWN,
                    AppEdge.ACTUATOR
            );


            application.addTupleMapping(
                    "fog_processor",
                    sensorTuple,
                    alertTuple,
                    new FractionalSelectivity(1.0)
            );
        }


        return application;
    }


    // ============================================================
    // CREATE FOG DEVICE
    // ============================================================

    private static FogDevice createFogDevice(
            String nodeName,
            long mips,
            int ram,
            long upBw,
            long downBw,
            int level,
            double ratePerMips,
            double busyPower,
            double idlePower
    ) {


        List<Pe> peList =
                new ArrayList<Pe>();


        peList.add(
                new Pe(
                        0,
                        new PeProvisionerOverbooking(
                                mips
                        )
                )
        );


        int hostId =
                FogUtils.generateEntityId();


        long storage =
                1000000;


        int bandwidth =
                10000;


        PowerHost host =
                new PowerHost(
                        hostId,
                        new RamProvisionerSimple(
                                ram
                        ),
                        new BwProvisionerOverbooking(
                                bandwidth
                        ),
                        storage,
                        peList,
                        new StreamOperatorScheduler(
                                peList
                        ),
                        new FogLinearPowerModel(
                                busyPower,
                                idlePower
                        )
                );


        List<Host> hostList =
                new ArrayList<Host>();


        hostList.add(host);


        FogDeviceCharacteristics characteristics =
                new FogDeviceCharacteristics(
                        "x86",
                        "Linux",
                        "Xen",
                        host,
                        10.0,
                        3.0,
                        0.05,
                        0.001,
                        0.0
                );


        FogDevice fogDevice =
                null;


        try {

            fogDevice =
                    new FogDevice(
                            nodeName,
                            characteristics,
                            new AppModuleAllocationPolicy(
                                    hostList
                            ),
                            new LinkedList<Storage>(),
                            10,
                            upBw,
                            downBw,
                            0,
                            ratePerMips
                    );


        } catch (Exception e) {

            e.printStackTrace();
        }


        fogDevice.setLevel(level);


        return fogDevice;
    }
}