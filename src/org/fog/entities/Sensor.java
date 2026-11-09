package org.fog.entities;

import java.util.ArrayList;
import java.util.Random;

import org.cloudbus.cloudsim.UtilizationModelFull;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.core.SimEntity;
import org.cloudbus.cloudsim.core.SimEvent;
import org.fog.application.AppEdge;
import org.fog.application.AppLoop;
import org.fog.application.Application;
import org.fog.utils.*;
import org.fog.utils.distribution.Distribution;

public class Sensor extends SimEntity {

    private int gatewayDeviceId;
    private GeoLocation geoLocation;
    private long outputSize;
    private String appId;
    private int userId;
    private String tupleType;
    private String sensorName;
    private String destModuleName;
    private Distribution transmitDistribution;
    private int controllerId;
    private Application app;
    private double latency;

    // ============================================================
    // DrainGuard dynamic sensor readings
    // ============================================================

    private double waterLevel;
    private double flowRate;
    private double rainfall;
    private double pressure;

    /*
     * Each sensor gets its own random generator.
     * The readings change slightly at every transmission.
     */
    private final Random random;

    private int transmissionStartDelay =
            Config.TRANSMISSION_START_DELAY;

    // ============================================================
    // Original iFogSim constructor
    // ============================================================

    public Sensor(
            String name,
            int userId,
            String appId,
            int gatewayDeviceId,
            double latency,
            GeoLocation geoLocation,
            Distribution transmitDistribution,
            int cpuLength,
            int nwLength,
            String tupleType,
            String destModuleName) {

        super(name);

        this.setAppId(appId);
        this.gatewayDeviceId = gatewayDeviceId;
        this.geoLocation = geoLocation;
        this.outputSize = 3;
        this.setTransmitDistribution(transmitDistribution);
        setUserId(userId);
        setDestModuleName(destModuleName);
        setTupleType(tupleType);
        setSensorName(name);
        setLatency(latency);

        this.random = new Random(name.hashCode());
    }

    // ============================================================
    // Original iFogSim constructor
    // ============================================================

    public Sensor(
            String name,
            int userId,
            String appId,
            int gatewayDeviceId,
            double latency,
            GeoLocation geoLocation,
            Distribution transmitDistribution,
            String tupleType) {

        super(name);

        this.setAppId(appId);
        this.gatewayDeviceId = gatewayDeviceId;
        this.geoLocation = geoLocation;
        this.outputSize = 3;
        this.setTransmitDistribution(transmitDistribution);
        setUserId(userId);
        setTupleType(tupleType);
        setSensorName(name);
        setLatency(latency);

        this.random = new Random(name.hashCode());
    }

    // ============================================================
    // Original iFogSim constructor
    // ============================================================

    public Sensor(
            String name,
            String tupleType,
            int userId,
            String appId,
            Distribution transmitDistribution) {

        super(name);

        this.setAppId(appId);
        this.setTransmitDistribution(transmitDistribution);
        setTupleType(tupleType);
        setSensorName(name);
        setUserId(userId);

        this.random = new Random(name.hashCode());
    }

    // ============================================================
    // DrainGuard constructor
    // ============================================================

    public Sensor(
            String name,
            String tupleType,
            int userId,
            String appId,
            Distribution transmitDistribution,
            double waterLevel,
            double flowRate,
            double rainfall,
            double pressure) {

        super(name);

        this.setAppId(appId);
        this.setTransmitDistribution(transmitDistribution);
        setTupleType(tupleType);
        setSensorName(name);
        setUserId(userId);

        this.waterLevel = waterLevel;
        this.flowRate = flowRate;
        this.rainfall = rainfall;
        this.pressure = pressure;

        /*
         * Different seed for every zone.
         * This makes Zone-1, Zone-2, etc. evolve differently.
         */
        this.random = new Random(name.hashCode());
    }

    // ============================================================
    // DrainGuard dynamic reading update
    // ============================================================

    private double changeValue(
            double current,
            double min,
            double max,
            double maximumChange) {

        /*
         * Random change between:
         *
         * -maximumChange and +maximumChange
         *
         * Example:
         * current = 85
         * maximumChange = 3
         *
         * next value can be approximately 82 to 88.
         */
        double change =
                (random.nextDouble() * 2.0 - 1.0)
                        * maximumChange;

        double newValue = current + change;

        // Keep value within realistic sensor limits.
        if (newValue < min) {
            newValue = min;
        }

        if (newValue > max) {
            newValue = max;
        }

        return Math.round(newValue * 100.0) / 100.0;
    }

    // ============================================================
    // Update DrainGuard readings
    // ============================================================

    private void updateDrainGuardReadings() {

        /*
         * Water level:
         * Changes slowly between 0 and 100.
         */
        waterLevel =
                changeValue(
                        waterLevel,
                        0.0,
                        100.0,
                        3.0
                );

        /*
         * Flow rate:
         * Changes between 0 and 100.
         */
        flowRate =
                changeValue(
                        flowRate,
                        0.0,
                        100.0,
                        4.0
                );

        /*
         * Rainfall:
         * Changes between 0 and 100.
         */
        rainfall =
                changeValue(
                        rainfall,
                        0.0,
                        100.0,
                        5.0
                );

        /*
         * Pressure:
         * Changes more slowly.
         */
        pressure =
                changeValue(
                        pressure,
                        0.0,
                        100.0,
                        2.5
                );
    }

    // ============================================================
    // TRANSMIT SENSOR DATA
    // ============================================================

    public void transmit() {

        // --------------------------------------------------------
        // IMPORTANT:
        // Update the four readings BEFORE creating the tuple.
        // Therefore every transmission contains new values.
        // --------------------------------------------------------

        updateDrainGuardReadings();

        AppEdge _edge = null;

        for (AppEdge edge : getApp().getEdges()) {

            if (edge.getSource().equals(getTupleType())) {
                _edge = edge;
                break;
            }
        }

        if (_edge == null) {
            return;
        }

        long cpuLength =
                (long) _edge.getTupleCpuLength();

        long nwLength =
                (long) _edge.getTupleNwLength();

        Tuple tuple =
                new Tuple(
                        getAppId(),
                        FogUtils.generateTupleId(),
                        Tuple.UP,
                        cpuLength,
                        1,
                        nwLength,
                        outputSize,
                        new UtilizationModelFull(),
                        new UtilizationModelFull(),
                        new UtilizationModelFull()
                );

        tuple.setUserId(getUserId());

        tuple.setTupleType(getTupleType());

        // --------------------------------------------------------
        // Attach current DrainGuard readings to the tuple
        // --------------------------------------------------------

        tuple.setWaterLevel(waterLevel);
        tuple.setFlowRate(flowRate);
        tuple.setRainfall(rainfall);
        tuple.setPressure(pressure);
        org.fog.test.perfeval.DrainGuardFogApp.recordSensorReading(
            org.cloudbus.cloudsim.core.CloudSim.clock(),
            getName(),
            waterLevel,
            flowRate,
            rainfall,
            pressure
        );

        tuple.setDestModuleName(
                _edge.getDestination()
        );

        tuple.setSrcModuleName(
                getSensorName()
        );

        // --------------------------------------------------------
        // Print the actual changing readings
        // --------------------------------------------------------

        System.out.println(
                "[iFogSim SENSOR] "
                + getSensorName()
                + " | Water="
                + waterLevel
                + " | Flow="
                + flowRate
                + " | Rain="
                + rainfall
                + " | Pressure="
                + pressure
        );

        Logger.debug(
                getName(),
                "Sending tuple with tupleId = "
                        + tuple.getCloudletId()
        );

        tuple.setDestinationDeviceId(
                getGatewayDeviceId()
        );

        int actualTupleId =
                updateTimings(
                        getSensorName(),
                        tuple.getDestModuleName()
                );

        tuple.setActualTupleId(actualTupleId);

        send(
                gatewayDeviceId,
                getLatency(),
                FogEvents.TUPLE_ARRIVAL,
                tuple
        );
    }

    // ============================================================
    // iFogSim timing
    // ============================================================

    protected int updateTimings(
            String src,
            String dest) {

        Application application = getApp();

        for (AppLoop loop : application.getLoops()) {

            if (loop.hasEdge(src, dest)) {

                int tupleId =
                        TimeKeeper
                                .getInstance()
                                .getUniqueId();

                if (!TimeKeeper
                        .getInstance()
                        .getLoopIdToTupleIds()
                        .containsKey(loop.getLoopId())) {

                    TimeKeeper
                            .getInstance()
                            .getLoopIdToTupleIds()
                            .put(
                                    loop.getLoopId(),
                                    new ArrayList<Integer>()
                            );
                }

                TimeKeeper
                        .getInstance()
                        .getLoopIdToTupleIds()
                        .get(loop.getLoopId())
                        .add(tupleId);

                TimeKeeper
                        .getInstance()
                        .getEmitTimes()
                        .put(
                                tupleId,
                                CloudSim.clock()
                        );

                return tupleId;
            }
        }

        return -1;
    }

    // ============================================================
    // START SENSOR
    // ============================================================

    @Override
    public void startEntity() {

        send(
                gatewayDeviceId,
                CloudSim.getMinTimeBetweenEvents(),
                FogEvents.SENSOR_JOINED,
                geoLocation
        );

        send(
                getId(),
                getTransmitDistribution().getNextValue()
                        + transmissionStartDelay,
                FogEvents.EMIT_TUPLE
        );
    }

    // ============================================================
    // PROCESS EVENTS
    // ============================================================

    @Override
    public void processEvent(SimEvent ev) {

        switch (ev.getTag()) {

            case FogEvents.TUPLE_ACK:

                break;

            case FogEvents.EMIT_TUPLE:

                /*
                 * Every time EMIT_TUPLE occurs:
                 *
                 * 1. Sensor readings change.
                 * 2. New tuple is created.
                 * 3. New readings are attached.
                 * 4. Tuple is sent to fog gateway.
                 */

                transmit();

                /*
                 * Schedule next sensor transmission.
                 *
                 * Your DrainGuardFogApp uses:
                 *
                 * SENSOR_TRANSMISSION_TIME = 10
                 *
                 * Therefore the next reading occurs
                 * every 10 simulation time units.
                 */

                send(
                        getId(),
                        getTransmitDistribution().getNextValue(),
                        FogEvents.EMIT_TUPLE
                );

                break;

            default:

                throw new IllegalStateException(
                        "Unexpected value: "
                                + ev.getTag()
                );
        }
    }

    // ============================================================
    // SHUTDOWN
    // ============================================================

    @Override
    public void shutdownEntity() {
    }

    // ============================================================
    // GETTERS / SETTERS
    // ============================================================

    public int getGatewayDeviceId() {
        return gatewayDeviceId;
    }

    public void setGatewayDeviceId(
            int gatewayDeviceId) {

        this.gatewayDeviceId = gatewayDeviceId;
    }

    public GeoLocation getGeoLocation() {
        return geoLocation;
    }

    public void setGeoLocation(
            GeoLocation geoLocation) {

        this.geoLocation = geoLocation;
    }

    public int getUserId() {
        return userId;
    }

    public void setUserId(int userId) {
        this.userId = userId;
    }

    public String getTupleType() {
        return tupleType;
    }

    public void setTupleType(String tupleType) {
        this.tupleType = tupleType;
    }

    public String getSensorName() {
        return sensorName;
    }

    public void setSensorName(String sensorName) {
        this.sensorName = sensorName;
    }

    public String getAppId() {
        return appId;
    }

    public void setAppId(String appId) {
        this.appId = appId;
    }

    public String getDestModuleName() {
        return destModuleName;
    }

    public void setDestModuleName(
            String destModuleName) {

        this.destModuleName = destModuleName;
    }

    public Distribution getTransmitDistribution() {
        return transmitDistribution;
    }

    public void setTransmitDistribution(
            Distribution transmitDistribution) {

        this.transmitDistribution =
                transmitDistribution;
    }

    public int getControllerId() {
        return controllerId;
    }

    public void setControllerId(
            int controllerId) {

        this.controllerId = controllerId;
    }

    public Application getApp() {
        return app;
    }

    public void setApp(Application app) {
        this.app = app;
    }

    public Double getLatency() {
        return latency;
    }

    public void setLatency(Double latency) {
        this.latency = latency;
    }

    protected long getOutputSize() {
        return this.outputSize;
    }

    // ============================================================
    // DrainGuard sensor getters
    // ============================================================

    public double getWaterLevel() {
        return waterLevel;
    }

    public void setWaterLevel(
            double waterLevel) {

        this.waterLevel = waterLevel;
    }

    public double getFlowRate() {
        return flowRate;
    }

    public void setFlowRate(
            double flowRate) {

        this.flowRate = flowRate;
    }

    public double getRainfall() {
        return rainfall;
    }

    public void setRainfall(
            double rainfall) {

        this.rainfall = rainfall;
    }

    public double getPressure() {
        return pressure;
    }

    public void setPressure(
            double pressure) {

        this.pressure = pressure;
    }

    public void setTransmissionStartDelay(
            int transmissionStartDelay) {

        this.transmissionStartDelay =
                transmissionStartDelay;
    }

    public int getTransmissionStartDelay() {
        return transmissionStartDelay;
    }
}