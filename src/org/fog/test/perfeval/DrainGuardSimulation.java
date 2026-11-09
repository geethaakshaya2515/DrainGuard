
package org.fog.test.perfeval;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.LinkedList;
import java.util.List;

import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.core.SimEntity;
import org.cloudbus.cloudsim.core.SimEvent;
import org.cloudbus.cloudsim.core.CloudActionTags;
import org.cloudbus.cloudsim.power.PowerHost;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;
import org.cloudbus.cloudsim.sdn.overbooking.BwProvisionerOverbooking;
import org.cloudbus.cloudsim.sdn.overbooking.PeProvisionerOverbooking;
import org.fog.entities.FogDevice;
import org.fog.entities.FogDeviceCharacteristics;
import org.fog.policy.AppModuleAllocationPolicy;
import org.fog.scheduler.StreamOperatorScheduler;
import org.fog.utils.FogLinearPowerModel;
import org.fog.utils.FogUtils;

public class DrainGuardSimulation {

    static List<FogDevice> fogDevices = new ArrayList<>();

    public static void main(String[] args) {

        try {
            System.out.println("==================================");
            System.out.println("       DRAINGUARD SIMULATION");
            System.out.println("==================================");

            List<ZoneTask> tasks = loadPredictions(
                "DrainGuard/ml_predictions.csv"
            );

            CloudSim.init(1, Calendar.getInstance(), false);

            FogDevice cloud = createFogDevice(
                "cloud", 40000, 40000, 10000, 10000,
                0, 16 * 103, 16 * 83.25
            );
            cloud.setParentId(-1);
            fogDevices.add(cloud);

            for (int i = 1; i <= 3; i++) {
                FogDevice fog = createFogDevice(
                    "fog-" + i, 4000, 4000, 10000, 10000,
                    1, 107.339, 83.4333
                );

                fog.setParentId(cloud.getId());
                fog.setUplinkLatency(10);
                fogDevices.add(fog);
            }

            System.out.println("\nML predictions loaded: " + tasks.size());
            System.out.println("Cloud servers: 1");
            System.out.println("Fog gateways: 3");

            // Event-driven DrainGuard processing entity
            new DrainageProcessor(tasks);

            System.out.println("\nStarting simulation...");
            CloudSim.startSimulation();
            CloudSim.stopSimulation();

            System.out.println("\nDrainGuard simulation completed.");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // Read the Python ML prediction CSV
    private static List<ZoneTask> loadPredictions(String path)
            throws Exception {

        List<ZoneTask> tasks = new ArrayList<>();

        try (BufferedReader reader = new BufferedReader(
                new FileReader(path))) {

            String line;
            reader.readLine(); // Skip CSV header

            while ((line = reader.readLine()) != null) {
                String[] values = line.split(",");

                if (values.length < 8) {
                    continue;
                }

                tasks.add(new ZoneTask(
                    values[0],
                    values[5],
                    values[6],
                    values[7],
                    false,
                    0
                ));
            }
        }

        if (tasks.isEmpty()) {
            throw new Exception("No ML predictions found in CSV!");
        }

        return tasks;
    }

    // Custom CloudSim entity for drainage processing events
    static class DrainageProcessor extends SimEntity {

        private final List<ZoneTask> tasks;
        private int fogCount = 0;
        private int cloudCount = 0;
        private double totalLatency = 0;

        DrainageProcessor(List<ZoneTask> tasks) {
            super("DrainGuard-Processor");
            this.tasks = tasks;
        }

        @Override
        public void startEntity() {
            super.startEntity();

            System.out.println("\nScheduling drainage events...");

            for (int i = 0; i < tasks.size(); i++) {
                ZoneTask task = tasks.get(i);

                task.arrivalTime = i + 1;

                schedule(
                    getId(),
                    i + 1,
                    CloudActionTags.SCHEDULE_NOW,
                    task
                );
            }
        }

        @Override
        public void processEvent(SimEvent event) {

            ZoneTask task = (ZoneTask) event.getData();

            if (!task.completed) {

                // Simulated service delay:
                // Fog = 2 time units; Cloud = 8 time units
                double delay = task.location.equalsIgnoreCase("FOG")
                    ? 2.0 : 8.0;

                task.completed = true;

                schedule(
                    getId(),
                    delay,
                    CloudActionTags.SCHEDULE_NOW,
                    task
                );

            } else {

                double latency = CloudSim.clock() - task.arrivalTime;
                totalLatency += latency;

                if (task.location.equalsIgnoreCase("FOG")) {
                    fogCount++;
                } else {
                    cloudCount++;
                }

                System.out.println(
                    "\nZone: " + task.zone +
                    " | Risk: " + task.risk +
                    " | Confidence: " + task.confidence + "%" +
                    " | Gateway: " + task.fogNode +
                    " | Processed at: " + task.location +
                    " | Simulated latency: " + latency
                );
            }
        }

        @Override
        public void shutdownEntity() {

            System.out.println("\n========== RESULTS ==========");
            System.out.println("Total zones processed: "
                + (fogCount + cloudCount));
            System.out.println("Fog processed: " + fogCount);
            System.out.println("Cloud processed: " + cloudCount);

            if (fogCount + cloudCount > 0) {
                System.out.println(
                    "Average simulated latency: " +
                    totalLatency / (fogCount + cloudCount)
                );
            }

            System.out.println("=============================");

            super.shutdownEntity();
        }
    }

    // Data carried by each simulation event
    static class ZoneTask {

        String zone;
        String risk;
        String confidence;
        String fogNode;
        String location;
        boolean completed;
        double arrivalTime;

        ZoneTask(
            String zone,
            String risk,
            String confidence,
            String fogNode,
            boolean completed,
            double arrivalTime
        ) {
            this.zone = zone;
            this.risk = risk;
            this.confidence = confidence;
            this.fogNode = fogNode;
            this.location = risk.equalsIgnoreCase("High")
                || risk.equalsIgnoreCase("Critical")
                ? "FOG" : "CLOUD";
            this.completed = completed;
            this.arrivalTime = arrivalTime;
        }
    }

    private static FogDevice createFogDevice(
        String name, long mips, int ram,
        long upBw, long downBw, int level,
        double busyPower, double idlePower
    ) throws Exception {

        List<Pe> peList = new ArrayList<>();
        peList.add(new Pe(0, new PeProvisionerOverbooking(mips)));

        int hostId = FogUtils.generateEntityId();

        PowerHost host = new PowerHost(
            hostId,
            new RamProvisionerSimple(ram),
            new BwProvisionerOverbooking(10000),
            1000000,
            peList,
            new StreamOperatorScheduler(peList),
            new FogLinearPowerModel(busyPower, idlePower)
        );

        List<Host> hostList = new ArrayList<>();
        hostList.add(host);

        FogDeviceCharacteristics characteristics =
            new FogDeviceCharacteristics(
                "x86", "Linux", "Xen", host,
                10.0, 3.0, 0.05, 0.001, 0.0
            );

        FogDevice device = new FogDevice(
            name,
            characteristics,
            new AppModuleAllocationPolicy(hostList),
            new LinkedList<Storage>(),
            10,
            upBw,
            downBw,
            0,
            0.01
        );

        device.setLevel(level);

        return device;
    }
}

