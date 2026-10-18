import time
import threading
import matplotlib.pyplot as plt


class Packet:
    """
    A class representing a simplified CAN bus packet.
    Parameters:
        - ecu_id: Identifier of the sending ECU.
        - id: Packet ID (lower value has higher priority).
        - payload: Payload data of the packet.
    """
    def __init__(self, ecu_id: int, id: int, payload: list):
        self.ecu_id = ecu_id
        self.id = id
        self.payload = payload


    def to_Array(self):
        return [self.ecu_id, self.id, self.payload]



class ECU:
    """
    A class representing an Electronic Control Unit (ECU) in a CAN bus network.

    Parameters:
        - ecu_id : Identifier of the ECU.
        - adversary_target_id : Target ECU ID for adversary attacks (-1 if not adversary) if the node is an adversary.

    Attributes:      
        - tec : Transmit Error Counter.
        - error_flag : Flag indicating if the ECU is currently in an error state.
        - retransmission : Flag indicating if the ECU needs to retransmit a packet.
        - retransmission_delay : Delay before retransmitting a packet (in seconds).
        - status : Current status of the ECU (ERROR_ACTIVE, ERROR_PASSIVE, BUS_OFF).
        - tec_history : List to store the history of TEC values for plotting.
        - sent_packets : Dictionary to store sent packets for later comparison (keyed by packet ID
            with values as tuples of (payload, packet)).
    """
    def __init__(self, ecu_id: int, adversary_target_id: int|None=None):
        self.adversary_target_id = adversary_target_id
        self.ecu_id = ecu_id
        self.tec = 0 
        self.error_flag = True
        self.retransmission = False
        self.retransmission_delay = 0.1
        self.status = 'ERROR_ACTIVE' 
        self.tec_history = []  
        self.sent_packets = {} 


    def update_status(self):
        """
        Check and update the status of the ECU based on TEC and REC values.
        """
        if self.tec <= 127:
            self.status = 'ERROR_ACTIVE'
        elif self.tec <= 254:
            self.status = 'ERROR_PASSIVE'
            self.retransmission_delay = 0.5
        else:
            self.status = 'BUS_OFF'


    def send_packet(self, packet_id: int, payload: bytes, canbus:'CANBus', retransmission=False):
        """
        Send a packet to the CAN bus.

        Parameters:
            - packet_id : ID of the packet to be sent.
            - payload : Payload of the packet.
            - canbus : CANBus object representing the network.
            - retransmission : True if the packet is a retransmission, False otherwise.
        """
        packet = Packet(self.ecu_id, packet_id, payload)
        
        if not retransmission:
            self.sent_packets[packet_id] = (payload, packet)

        with canbus.lock:
            canbus.packet_log.append(packet)
            if retransmission:
                print(f"ECU with ID={self.ecu_id} is sending packet with payload={payload}")
                print(f"ECU {self.ecu_id} TEC = {self.tec}")
            else:
                print(f"ECU with ID={self.ecu_id} is sending packet with payload={payload}")
                print(f"ECU {self.ecu_id} TEC = {self.tec}")
      

    def check_duplicate_ids(self, packet_id: int, canbus: 'CANBus'):
        """
        Check the CAN bus log for duplicate packet IDs and set retransmission flags if needed.

        Parameters:
            - packet_id : ID of the packet to check for duplicates.
            - canbus : CANBus object representing the network.
        """
        with canbus.lock:
            duplicates = [msg for msg in canbus.packet_log if msg.id == packet_id and msg.ecu_id != self.ecu_id]
            
            if len(duplicates) > 0:                
                for duplicate in duplicates:
                    original_payload, original_packet = self.sent_packets[packet_id]
                    if duplicate.to_Array() != original_packet.to_Array():
                        self.retransmission = True
            else:   
                self.retransmission = False


    def update_tec(self, packet_id: int, canbus: 'CANBus'):
        """
        Update the TEC counter based on the CAN bus communication outcomes.

        Parameters:
            - packet_id : ID of the packet being checked.
            - canbus : CANBus object representing the network.
        """
        with canbus.lock:
            duplicates = [msg for msg in canbus.packet_log if msg.id == packet_id and msg.ecu_id != self.ecu_id]
            
            if len(duplicates) > 0:                
                for duplicate in duplicates:
                    original_payload, original_packet = self.sent_packets[packet_id]
                    if duplicate.to_Array() != original_packet.to_Array():
                        if not self.adversary_target_id:
                            if self.status == 'ERROR_ACTIVE' and self.error_flag == True:
                                self.tec += 8
                                self.tec_history.append({'time': time.time(), 'tec': self.tec})
                            elif self.status == 'ERROR_PASSIVE' and self.error_flag == True:
                                self.tec += 8
                                self.tec_history.append({'time': time.time(), 'tec': self.tec})
                                self.tec -= 1
                                self.tec_history.append({'time': time.time(), 'tec': self.tec})
                                self.error_flag = False
                            elif self.status == 'ERROR_PASSIVE' and self.error_flag == False:
                                self.tec += 8
                                self.tec_history.append({'time': time.time(), 'tec': self.tec})
                                self.tec -= 1
                                self.tec_history.append({'time': time.time(), 'tec': self.tec})
                        else:
                            if self.status == 'ERROR_ACTIVE' and self.error_flag == True:
                                self.tec += 8
                                self.tec_history.append({'time': time.time(), 'tec': self.tec})
                            elif self.status == 'ERROR_PASSIVE' or (self.status == 'ERROR_ACTIVE' and self.error_flag == False):
                                self.tec -= 1
                                self.tec_history.append({'time': time.time(), 'tec': self.tec})
                                self.error_flag = False
            self.update_status()


    def run_ecu(self, packet_id: int, payload: list, canbus: 'CANBus', barrier: threading.Barrier):
        """
        Simulate the behavior of an ECU, including sending packets and handling errors 
        throug ECU functions.

        Parameters:
            - ecu : The ECU object representing the node in the CAN bus.
            - packet_id : The ID of the packet to be sent by the ECU.
            - payload : The payload data to be sent in the packet.
            - canbus : The shared CAN bus object connecting all ECUs.
            - barrier : A threading barrier used to synchronize ECUs' actions.
        """
        simulation_state = 'running'
        while simulation_state == 'running' and canbus.is_ecu_connected(self) and len(canbus.ecus) > 1:
            canbus.packet_log.clear()
            
            self.update_status()
            
            if self.status == 'BUS_OFF':
                with canbus.lock:
                    canbus.disconnect_ecu(self)
                simulation_state = 'stopped'
                break
            
            try:
                barrier.wait(timeout=1)   
            
                if self.retransmission:
                    self.send_packet(packet_id, self.sent_packets[packet_id][1].payload, canbus, retransmission=True)
                else:
                    self.send_packet(packet_id, payload, canbus)

                barrier.wait(timeout=1)   

                self.check_duplicate_ids(packet_id, canbus)

                barrier.wait(timeout=1)   

            except threading.BrokenBarrierError:
                barrier.reset()
                continue

            self.update_tec(packet_id, canbus)
            
            time.sleep(self.retransmission_delay)



class CANBus:
    """
    A class representing a CAN bus network that connects multiple ECUs.
    Attributes:
        - ecus : List of ECUs currently connected to the CAN bus.
        - packet_log : List of packets sent on the CAN bus for the current time step.
        - lock : A threading lock to synchronize access to the CAN bus resources.
    """

    def __init__(self):
        self.ecus = []
        self.packet_log = []
        self.lock = threading.Lock()

    def connect_ecu(self, ecu:ECU):
        if ecu not in self.ecus:
            self.ecus.append(ecu)
            print(f"The ECU {ecu.ecu_id} has been connected to the CAN bus")

    def disconnect_ecu(self, ecu:ECU):
        if ecu in self.ecus:
            self.ecus.remove(ecu)
            print(f"The ECU {ecu.ecu_id} has been disconnected from the CAN bus")

    def is_ecu_connected(self, ecu:ECU):
        return ecu in self.ecus



def plot_tec_history(*ecus):
    """
    Plot TEC history of the ECUs passed as parameters.

    Parameters:
    - ecus: The ECUs objects.
    """
    plt.figure(figsize=(8,6))

    for ecu in ecus:
        if not ecu.tec_history:
            print(f"Warning: No TEC history for ECU {ecu.ecu_id}")
            continue

        times = [entry['time'] for entry in ecu.tec_history]
        tec_values = [entry['tec'] for entry in ecu.tec_history]

        normalized_times = [t - times[0] for t in times]

        if ecu.adversary_target_id:
            plt.plot(normalized_times,tec_values,label=f"ECU {ecu.ecu_id} (Adversary)")
        else:
            plt.plot(normalized_times,tec_values,label=f"ECU {ecu.ecu_id} (Victim)")

    plt.xlabel("Time (s)")
    plt.ylabel("Transmit Error Counter")
    plt.title("TEC Over Time")
    plt.legend()
    plt.grid(True, axis='y')

    plt.xlim(left=0)
    plt.ylim(bottom=0)

    plt.savefig('tec_plot.png', dpi=200, bbox_inches='tight')

    plt.show()


canbus = CANBus()
victim = ECU(1)
adversary = ECU(2, adversary_target_id=1)

canbus.connect_ecu(victim)
canbus.connect_ecu(adversary)

barrier = threading.Barrier(2)

thread1 = threading.Thread(target=victim.run_ecu, args=(1, [1,1,1,1,1,1,1,1], canbus, barrier))
thread2 = threading.Thread(target=adversary.run_ecu, args=(1, [1,1,0,0,0,0,0,0], canbus, barrier))

thread1.start()
thread2.start()

thread1.join()
thread2.join()

plot_tec_history(victim, adversary)
