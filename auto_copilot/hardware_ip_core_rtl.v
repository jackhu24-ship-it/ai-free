// =============================================================================
// Company:      AutoCopilot Semiconductor Safety Division
// Module Name:  Safety_Fast_Abort_Arbiter_Core
// Standard:     IEEE 1364-2001 (Verilog-2001) / ASIL-D Synthesizable RTL
// Target:       Infineon AURIX TC4xx / NXP S32G / ST Stellar Silicon IP Core
// Description:  Dedicated Hardware IP Core for deterministic sub-microsecond
//               actuator power cutoff, hardware envelope checking, and
//               direct Non-Maskable Interrupt (NMI) asserting.
// =============================================================================

	imescale 1ns / 1ps

module Safety_Fast_Abort_Arbiter_Core #(
    parameter integer CLK_FREQ_MHZ       = 400,          // 400 MHz Vehicle Core Clock (2.5ns period)
    parameter [31:0]  HSM_UNLOCK_MAGIC   = 32'hA55A_BEEF // Secure HSM Unlock Key
)(
    input  wire        clk,                 // System Clock (200 - 400 MHz)
    input  wire        rst_n,               // Active-Low Reset (Safety Power-on-Reset)

    // Actuator Command Bus
    input  wire [15:0] i_torque_cmd,        // Raw Actuator Torque Command
    input  wire        i_torque_valid,      // Torque Command Valid Strobe
    input  wire [15:0] i_envelope_max,      // Upper Dynamic Safe Envelope Limit

    // Real-Time Bus & Physical Fault Indicators
    input  wire        i_e2e_crc_err,       // E2E CRC Checksum Mismatch Flag
    input  wire        i_roll_cnt_err,      // Rolling Counter Jitter/Loss Flag
    input  wire        i_ext_fault_n,       // Active-Low External Hardware Kill (Watchdog)

    // Secure HSM Interface for Post-Trip Recovery
    input  wire [31:0] i_hsm_unlock_key,    // HSM Authorization Key
    input  wire        i_hsm_clear_trip,    // Reset Trip Strobe

    // Actuator Gate Driver Outputs
    output reg         o_power_stage_en,    // 1: Normal Drive, 0: Hard Cutoff to Safe State
    output reg         o_safe_state_tripped,// Latched Safe State Status
    output reg         o_nmi_irq,           // Direct Level/Pulse NMI to TriCore / ARM Cortex-R52
    output reg  [3:0]  o_trip_reason,       // Fault Reason Code
    output reg  [7:0]  o_cycle_latency      // Measured Cycle Delay (Deterministic = 1 Cycle)
);

    // Trip Reason Encoding
    localparam [3:0] REASON_NONE       = 4'b0000;
    localparam [3:0] REASON_CRC_ERR    = 4'b0001;
    localparam [3:0] REASON_CNT_ERR    = 4'b0010;
    localparam [3:0] REASON_OVERTORQUE = 4'b0011;
    localparam [3:0] REASON_EXT_FAULT  = 4'b0100;

    // Internal Combinational Fault Evaluation
    wire fault_detected;
    wire [3:0] fault_cause;

    assign fault_detected = (i_e2e_crc_err == 1'b1)  ||
                            (i_roll_cnt_err == 1'b1) ||
                            (i_ext_fault_n == 1'b0)  ||
                            (i_torque_valid && (i_torque_cmd > i_envelope_max));

    assign fault_cause = (i_e2e_crc_err == 1'b1)                        ? REASON_CRC_ERR :
                         (i_roll_cnt_err == 1'b1)                       ? REASON_CNT_ERR :
                         (i_ext_fault_n == 1'b0)                        ? REASON_EXT_FAULT :
                         (i_torque_valid && (i_torque_cmd > i_envelope_max)) ? REASON_OVERTORQUE :
                                                                          REASON_NONE;

    // Synchronous Hardware Latch
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            o_power_stage_en     <= 1'b0; // Fail-Safe on Reset
            o_safe_state_tripped <= 1'b1; // Default to Latched Trip
            o_nmi_irq            <= 1'b0;
            o_trip_reason        <= REASON_NONE;
            o_cycle_latency      <= 8'd0;
        end else begin
            if (fault_detected) begin
                // Deterministic 1-Cycle Hardware Cutoff (2.5ns @ 400MHz)
                o_power_stage_en     <= 1'b0;
                o_safe_state_tripped <= 1'b1;
                o_nmi_irq            <= 1'b1;
                o_trip_reason        <= fault_cause;
                o_cycle_latency      <= 8'd1;
            end else if (o_safe_state_tripped) begin
                // Hold Latched Safe State until Authenticated HSM Clear
                o_power_stage_en <= 1'b0;
                o_nmi_irq        <= 1'b0; // De-assert NMI pulse after triggering
                if (i_hsm_clear_trip && (i_hsm_unlock_key == HSM_UNLOCK_MAGIC)) begin
                    o_safe_state_tripped <= 1'b0;
                    o_trip_reason        <= REASON_NONE;
                    o_power_stage_en     <= 1'b1; // Normal Re-enable
                    o_cycle_latency      <= 8'd0;
                end
            end else begin
                // Normal Operation Envelope
                o_power_stage_en     <= 1'b1;
                o_safe_state_tripped <= 1'b0;
                o_nmi_irq            <= 1'b0;
                o_trip_reason        <= REASON_NONE;
                o_cycle_latency      <= 8'd0;
            end
        end
    end

endmodule
