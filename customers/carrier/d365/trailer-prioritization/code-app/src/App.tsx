import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  makeStyles,
  tokens,
  DataGrid,
  DataGridHeader,
  DataGridRow,
  DataGridHeaderCell,
  DataGridBody,
  DataGridCell,
  TableColumnDefinition,
  createTableColumn,
  Button,
  Badge,
  Spinner,
  Text,
  Slider,
  Checkbox,
} from "@fluentui/react-components";
import {
  ArrowSync24Regular,
  Calendar24Regular,
  VehicleTruckProfile24Regular,
} from "@fluentui/react-icons";
import { useQuery } from "@tanstack/react-query";

// ─── Types ────────────────────────────────────────────────────────────────────
interface Trailer {
  carr_trailerid: string;
  carr_factorysupplier: string;
  carr_otifscore: number;
  carr_revenueimpact: number;
  carr_compositescore: number;
  carr_priorityrank: number;
  carr_schedulestatus: string;
  carr_assigneddock: string;
  carr_scheduleddate?: string;
  carr_shipdate?: string;
  carr_approvedoverflow?: boolean;
}

interface SimulatedTrailer extends Trailer {
  simulatedRank: number;
  recommendedDock: string;
  recommendedWindow: string;
  recommendedAction: string;
  factors: {
    slaRisk: number;
    revenueWeight: number;
    arrivalRisk: number;
    dockConstraint: number;
    laborPressure: number;
    readiness: number;
  };
}

interface DispatchStop {
  trailerId: string;
  supplier: string;
  dock: string;
  window: string;
  eta: string;
  action: string;
}

interface ScenarioSettings {
  lateArrivalRisk: number;
  laborCapacity: number;
  slaUrgency: number;
  dockOutage: boolean;
}

interface ImpactMetrics {
  detentionAvoided: number;
  breachesPrevented: number;
  projectedUtilization: number;
  queueReductionMinutes: number;
  baseUtilization: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────
const DEFAULT_SCENARIO: ScenarioSettings = {
  lateArrivalRisk: 35,
  laborCapacity: 82,
  slaUrgency: 70,
  dockOutage: false,
};

const PLAN_WINDOWS = ["08:00", "08:45", "09:30", "10:15", "11:00", "11:45", "12:30"];

// ─── Styles ──────────────────────────────────────────────────────────────────
const useStyles = makeStyles({
  app: {
    minHeight: "100vh",
    background: "radial-gradient(circle at 0% 0%, #dcecff 0%, #f4f8ff 35%, #eef3fb 100%)",
    fontFamily: '"Segoe UI Variable", "Segoe UI", "Bahnschrift", sans-serif',
  },
  page: {
    display: "grid",
    gridTemplateRows: "auto 1fr",
    minHeight: "100vh",
    gap: "16px",
    paddingBottom: "24px",
  },
  header: {
    background: "linear-gradient(120deg, #07283f 0%, #004680 45%, #0b6ac7 100%)",
    padding: "0 24px",
    minHeight: "84px",
    display: "flex",
    alignItems: "center",
    boxShadow: "0 10px 30px rgba(0, 41, 74, 0.28)",
  },
  headerContent: {
    width: "100%",
    maxWidth: "1400px",
    margin: "0 auto",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "12px",
    padding: "14px 0",
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  headerText: {
    display: "grid",
    gap: "2px",
  },
  headerEyebrow: {
    color: "#d1ecff",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    fontSize: "11px",
    fontWeight: 700,
  },
  headerTitle: {
    color: "white",
    fontSize: "19px",
    fontWeight: 700,
    lineHeight: 1.2,
  },
  headerSubtitle: {
    color: "#b9ddff",
    fontSize: "12px",
  },
  headerPillRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap",
  },
  headerPill: {
    color: "#d8efff",
    fontSize: "11px",
    fontWeight: 700,
    border: "1px solid rgba(202, 233, 255, 0.35)",
    borderRadius: "999px",
    padding: "4px 10px",
    backgroundColor: "rgba(255, 255, 255, 0.1)",
  },
  contentWrap: {
    width: "100%",
    maxWidth: "1400px",
    margin: "0 auto",
    display: "grid",
    gap: "16px",
    padding: "0 24px",
  },
  heroGrid: {
    display: "grid",
    gridTemplateColumns: "1.45fr 0.85fr",
    gap: "16px",
  },
  panel: {
    backgroundColor: "rgba(255,255,255,0.95)",
    borderRadius: "16px",
    border: `1px solid ${tokens.colorNeutralStrokeAccessible}`,
    boxShadow: "0 8px 24px rgba(0, 25, 46, 0.08)",
    backdropFilter: "blur(4px)",
  },
  scenarioPanel: {
    padding: "20px",
    display: "grid",
    gap: "16px",
  },
  panelTitleRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "12px",
  },
  panelTitle: {
    fontSize: "18px",
    fontWeight: 700,
    color: "#0f172a",
  },
  panelSubtitle: {
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase200,
  },
  sliderGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
  },
  sliderCard: {
    borderRadius: "10px",
    backgroundColor: "#f8fbff",
    border: "1px solid #deebf7",
    padding: "13px",
    display: "grid",
    gap: "10px",
  },
  sliderLabelRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  summaryBand: {
    background: "linear-gradient(120deg, #edf6ff 0%, #f7fbff 100%)",
    borderRadius: "8px",
    border: "1px solid #d6e8fa",
    padding: "10px 12px",
    display: "grid",
    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
    gap: "8px",
  },
  summaryChip: {
    fontSize: "11px",
    fontWeight: 700,
    color: "#004680",
    backgroundColor: "rgba(255,255,255,0.7)",
    borderRadius: "999px",
    padding: "5px 8px",
    textAlign: "center",
  },
  explanationPanel: {
    padding: "18px",
    display: "grid",
    gap: "14px",
  },
  explanationHero: {
    display: "grid",
    gap: "8px",
  },
  explanationGrid: {
    display: "grid",
    gap: "12px",
  },
  factorRow: {
    display: "grid",
    gridTemplateColumns: "80px 1fr 60px",
    gap: "8px",
    alignItems: "center",
    fontSize: "12px",
  },
  factorTrack: {
    height: "8px",
    backgroundColor: "#e8ebf0",
    borderRadius: "999px",
    overflow: "hidden",
  },
  factorFill: {
    height: "100%",
    borderRadius: "999px",
    background: "linear-gradient(90deg, #0b7ad1 0%, #4fb7ff 100%)",
  },
  focusCard: {
    display: "grid",
    gap: "12px",
    padding: "20px",
    background: "linear-gradient(145deg, #ffffff 0%, #f6fbff 100%)",
  },
  focusCardTitle: {
    fontSize: "14px",
    fontWeight: 600,
    color: "#0f172a",
  },
  focusCardSubtitle: {
    fontSize: "11px",
    color: tokens.colorNeutralForeground3,
  },
  focusTrailerRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px 0",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  focusBadgeRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap",
  },
  focusNote: {
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase200,
  },
  timelinePanel: {
    padding: "18px",
    display: "grid",
    gap: "14px",
  },
  timelineHeader: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "8px",
  },
  timelineTitle: {
    fontSize: "16px",
    fontWeight: 700,
    color: "#0f172a",
  },
  timelineSubtitle: {
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase200,
  },
  timelineGrid: {
    display: "grid",
    gridTemplateColumns: "120px 1fr",
    gap: "12px",
    fontSize: "11px",
  },
  dockLabel: {
    paddingRight: "8px",
    fontWeight: 600,
    color: "#004680",
    height: "80px",
    display: "flex",
    alignItems: "center",
  },
  timelineHours: {
    display: "flex",
    gap: "1px",
    backgroundColor: tokens.colorNeutralStroke2,
    borderRadius: "8px",
    overflow: "hidden",
  },
  timeHour: {
    flex: "1 1 0",
    paddingTop: "4px",
    paddingBottom: "8px",
    backgroundColor: "#f8fbff",
    textAlign: "center",
    borderRight: `1px solid ${tokens.colorNeutralStroke2}`,
    fontWeight: 600,
    color: "#0b7ad1",
    fontSize: "10px",
  },
  dockLane: {
    display: "flex",
    gap: "1px",
    backgroundColor: tokens.colorNeutralStroke2,
    borderRadius: "8px",
    overflow: "hidden",
    height: "80px",
  },
  laneBucket: {
    flex: "1 1 0",
    backgroundColor: "#fbfdff",
    padding: "4px",
    display: "flex",
    flexDirection: "column",
    gap: "2px",
    borderRight: `1px solid ${tokens.colorNeutralStroke2}`,
    fontSize: "9px",
    overflow: "hidden",
  },
  trailerBlock: {
    padding: "3px 4px",
    borderRadius: "4px",
    backgroundColor: "#0b7ad1",
    color: "white",
    fontWeight: 600,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    fontSize: "8px",
  },
  trailerBlockHighRank: {
    backgroundColor: "#004680",
  },
  trailerBlockOverflow: {
    backgroundColor: "#ff7c3b",
  },
  trailerBlockUnscheduled: {
    backgroundColor: "#d13438",
  },
  kpiRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
    gap: "16px",
  },
  kpiCard: {
    backgroundColor: "rgba(255,255,255,0.95)",
    borderRadius: "12px",
    padding: "16px",
    border: `1px solid ${tokens.colorNeutralStrokeAccessible}`,
    boxShadow: "0 5px 18px rgba(15, 32, 56, 0.06)",
  },
  kpiNumber: {
    fontSize: "32px",
    fontWeight: "700",
    lineHeight: "1",
    marginBottom: "4px",
  },
  contentGrid: {
    display: "grid",
    gridTemplateColumns: "1.55fr 1fr",
    gap: "16px",
  },
  tablePanel: {
    overflow: "hidden",
  },
  toolbar: {
    padding: "14px 18px",
    display: "flex",
    gap: "12px",
    alignItems: "center",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: "#f8fbff",
  },
  '@media (max-width: 1200px)': {
    heroGrid: {
      gridTemplateColumns: "1fr",
    },
    contentGrid: {
      gridTemplateColumns: "1fr",
    },
  },
  '@media (max-width: 980px)': {
    sliderGrid: {
      gridTemplateColumns: "1fr",
    },
    kpiRow: {
      gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    },
    summaryBand: {
      gridTemplateColumns: "1fr",
    },
    contentWrap: {
      padding: "0 12px",
    },
  },
  '@media (max-width: 720px)': {
    kpiRow: {
      gridTemplateColumns: "1fr",
    },
    headerContent: {
      alignItems: "flex-start",
      flexDirection: "column",
    },
  },
  tableWrap: {
    padding: "0 8px 8px",
  },
  dispatchPanel: {
    padding: "18px",
    display: "grid",
    gap: "14px",
  },
  dispatchList: {
    display: "grid",
    gap: "10px",
  },
  dispatchItem: {
    borderRadius: "12px",
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    padding: "12px 14px",
    display: "grid",
    gap: "6px",
    backgroundColor: "#fbfdff",
  },
  exceptionPanel: {
    padding: "18px",
    display: "grid",
    gap: "12px",
  },
  exceptionList: {
    display: "grid",
    gap: "10px",
  },
  exceptionItem: {
    borderRadius: "12px",
    padding: "12px 14px",
    border: "1px solid #ffd8b2",
    backgroundColor: "#fff8f2",
    display: "grid",
    gap: "10px",
  },
  footerNote: {
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase200,
  },
});

// ─── Status badge helper ──────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const color =
    status === "Confirmed"
      ? "success"
      : status === "Scheduled"
      ? "informative"
      : status === "Rescheduled"
      ? "danger"
      : status === "Overflow"
      ? "warning"
      : "subtle";
  return (
    <Badge appearance="filled" color={color as any}>
      {status}
    </Badge>
  );
}

// ─── KPI Card ────────────────────────────────────────────────────────────────
function KPICard({
  label,
  value,
  delta,
  color,
}: {
  label: string;
  value: string;
  delta?: string;
  color?: string;
}) {
  const styles = useStyles();
  return (
    <div className={styles.kpiCard}>
      <div className={styles.kpiNumber} style={{ color: color ?? "#004680" }}>
        {value}
      </div>
      <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
        {label}
      </Text>
      {delta && (
        <Text size={100} style={{ color: "#107c10", fontWeight: 600 }}>
          {delta}
        </Text>
      )}
    </div>
  );
}

// ─── Helper Functions ─────────────────────────────────────────────────────────
function formatThousands(n: number): string {
  return `$${(n / 1000).toFixed(1)}K`;
}

function formatDelta(n: number, suffix = ""): string {
  return n >= 0 ? `+${n}${suffix}` : `${n}${suffix}`;
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

function isScheduled(status: string): boolean {
  return status === "Scheduled" || status === "Confirmed";
}

function scenarioCapacity(scenario: ScenarioSettings): number {
  const base = 8;
  const laborBonus = (scenario.laborCapacity - 50) * 0.15;
  const riskPenalty = (scenario.lateArrivalRisk / 100) * 2;
  return Math.round(base + laborBonus - riskPenalty);
}

function buildSimulation(
  trailers: Trailer[],
  scenario: ScenarioSettings
): SimulatedTrailer[] {
  return trailers
    .map((trailer, index) => {
      const slaRisk = (scenario.slaUrgency / 100) * 12 + (Math.random() * 4 - 2);
      const revenueWeight = (trailer.carr_revenueimpact / 50000) * 8;
      const arrivalRisk = (scenario.lateArrivalRisk / 100) * 8;
      const dockConstraint = scenario.dockOutage ? 6 : 2 + Math.random() * 2;
      const laborPressure = (100 - scenario.laborCapacity) / 100 * 6;
      const readiness = (trailer.carr_otifscore / 5) * 8;

      const recommendedDock =
        index % 3 === 0 && !scenario.dockOutage
          ? "Dock 1"
          : index % 3 === 1
          ? "Dock 2"
          : "Overflow";

      const recommendedAction =
        trailer.carr_schedulestatus === "Unscheduled"
          ? "Schedule now"
          : trailer.carr_schedulestatus === "Rescheduled"
          ? "Reconfirm and reslot"
          : trailer.carr_schedulestatus === "Overflow"
          ? "Overflow approval"
          : "Hold current slot";

      return {
        ...trailer,
        simulatedRank: index + 1,
        recommendedDock,
        recommendedWindow: PLAN_WINDOWS[index % PLAN_WINDOWS.length] ?? "Later today",
        recommendedAction,
        factors: {
          slaRisk: clamp(slaRisk, 0, 12),
          revenueWeight: clamp(revenueWeight, 0, 8),
          arrivalRisk: clamp(arrivalRisk, 0, 8),
          dockConstraint: clamp(dockConstraint, 0, 8),
          laborPressure: clamp(laborPressure, 0, 6),
          readiness: clamp(readiness, 0, 8),
        },
      };
    })
    .sort((a, b) => b.factors.slaRisk - a.factors.slaRisk);
}

function buildImpactMetrics(
  original: Trailer[],
  simulated: SimulatedTrailer[],
  scenario: ScenarioSettings
): ImpactMetrics {
  const capacity = scenarioCapacity(scenario);
  const planCandidates = simulated.filter((t) => !isScheduled(t.carr_schedulestatus)).slice(0, capacity);

  const baseUtilization = Math.round((original.filter((t) => isScheduled(t.carr_schedulestatus)).length / original.length) * 100);
  const projectedUtilization = Math.round(
    ((original.filter((t) => isScheduled(t.carr_schedulestatus)).length + planCandidates.length) / original.length) * 100
  );

  return {
    detentionAvoided: planCandidates.reduce((sum, t) => sum + (t.carr_revenueimpact ?? 0), 0),
    breachesPrevented: planCandidates.filter((t) => t.factors.slaRisk > 8).length,
    projectedUtilization,
    queueReductionMinutes: planCandidates.length * 45,
    baseUtilization,
  };
}

function buildDispatchPlan(
  simulated: SimulatedTrailer[],
  _scenario: ScenarioSettings
): DispatchStop[] {
  return simulated.slice(0, 12).map((trailer, idx) => ({
    trailerId: trailer.carr_trailerid,
    supplier: trailer.carr_factorysupplier,
    dock: trailer.recommendedDock,
    window: PLAN_WINDOWS[idx % PLAN_WINDOWS.length] ?? "Later today",
    eta: `${8 + Math.floor((idx / 2) * 0.75)}:${String((idx * 15) % 60).padStart(2, "0")}`,
    action: trailer.recommendedAction,
  }));
}

function buildExceptions(
  simulated: SimulatedTrailer[],
  _scenario: ScenarioSettings
): Array<{ type: string; trailer: SimulatedTrailer }> {
  const exceptions: Array<{ type: string; trailer: SimulatedTrailer }> = [];

  simulated
    .filter((t) => t.factors.slaRisk > 10)
    .slice(0, 3)
    .forEach((trailer) => {
      exceptions.push({ type: "SLA Risk — High", trailer });
    });

  simulated
    .filter((t) => t.carr_schedulestatus === "Unscheduled")
    .slice(0, 2)
    .forEach((trailer) => {
      exceptions.push({ type: "Unscheduled — Needs Action", trailer });
    });

  return exceptions;
}

// ─── Data hooks ────────────────────────────────────────────────────────────────
function useTrailers() {
  return useQuery<Trailer[]>({
    queryKey: ["trailers"],
    queryFn: async () => {
      // Return mock data for demo
      return [
        {
          carr_trailerid: "CARR-001",
          carr_factorysupplier: "Factory A",
          carr_otifscore: 4,
          carr_revenueimpact: 45000,
          carr_compositescore: 22.1,
          carr_priorityrank: 1,
          carr_schedulestatus: "Scheduled",
          carr_assigneddock: "Dock 1",
        },
        {
          carr_trailerid: "CARR-002",
          carr_factorysupplier: "Factory B",
          carr_otifscore: 5,
          carr_revenueimpact: 38000,
          carr_compositescore: 20.5,
          carr_priorityrank: 2,
          carr_schedulestatus: "Confirmed",
          carr_assigneddock: "Dock 2",
        },
        {
          carr_trailerid: "CARR-003",
          carr_factorysupplier: "Factory C",
          carr_otifscore: 5,
          carr_revenueimpact: 62000,
          carr_compositescore: 24.4,
          carr_priorityrank: 3,
          carr_schedulestatus: "Unscheduled",
          carr_assigneddock: "",
        },
        {
          carr_trailerid: "CARR-004",
          carr_factorysupplier: "Factory D",
          carr_otifscore: 3,
          carr_revenueimpact: 27000,
          carr_compositescore: 17.2,
          carr_priorityrank: 4,
          carr_schedulestatus: "Scheduled",
          carr_assigneddock: "Dock 2",
        },
        {
          carr_trailerid: "CARR-005",
          carr_factorysupplier: "Factory E",
          carr_otifscore: 4,
          carr_revenueimpact: 51000,
          carr_compositescore: 21.8,
          carr_priorityrank: 5,
          carr_schedulestatus: "Rescheduled",
          carr_assigneddock: "Dock 1",
        },
        {
          carr_trailerid: "CARR-006",
          carr_factorysupplier: "Factory F",
          carr_otifscore: 2,
          carr_revenueimpact: 18000,
          carr_compositescore: 13.4,
          carr_priorityrank: 6,
          carr_schedulestatus: "Overflow",
          carr_assigneddock: "Overflow",
        },
        {
          carr_trailerid: "CARR-007",
          carr_factorysupplier: "Factory G",
          carr_otifscore: 5,
          carr_revenueimpact: 71000,
          carr_compositescore: 26.1,
          carr_priorityrank: 7,
          carr_schedulestatus: "Unscheduled",
          carr_assigneddock: "",
        },
        {
          carr_trailerid: "CARR-008",
          carr_factorysupplier: "Factory H",
          carr_otifscore: 4,
          carr_revenueimpact: 33000,
          carr_compositescore: 18.9,
          carr_priorityrank: 8,
          carr_schedulestatus: "Scheduled",
          carr_assigneddock: "Dock 2",
        },
        {
          carr_trailerid: "CARR-009",
          carr_factorysupplier: "Factory I",
          carr_otifscore: 3,
          carr_revenueimpact: 29000,
          carr_compositescore: 16.7,
          carr_priorityrank: 9,
          carr_schedulestatus: "Confirmed",
          carr_assigneddock: "Dock 1",
        },
        {
          carr_trailerid: "CARR-010",
          carr_factorysupplier: "Factory J",
          carr_otifscore: 5,
          carr_revenueimpact: 84000,
          carr_compositescore: 28.5,
          carr_priorityrank: 10,
          carr_schedulestatus: "Unscheduled",
          carr_assigneddock: "",
        },
        {
          carr_trailerid: "CARR-011",
          carr_factorysupplier: "Factory K",
          carr_otifscore: 2,
          carr_revenueimpact: 14000,
          carr_compositescore: 11.1,
          carr_priorityrank: 11,
          carr_schedulestatus: "Overflow",
          carr_assigneddock: "Overflow",
        },
        {
          carr_trailerid: "CARR-012",
          carr_factorysupplier: "Factory L",
          carr_otifscore: 4,
          carr_revenueimpact: 39000,
          carr_compositescore: 19.3,
          carr_priorityrank: 12,
          carr_schedulestatus: "Rescheduled",
          carr_assigneddock: "Dock 2",
        },
        {
          carr_trailerid: "CARR-013",
          carr_factorysupplier: "Factory M",
          carr_otifscore: 3,
          carr_revenueimpact: 25000,
          carr_compositescore: 15.5,
          carr_priorityrank: 13,
          carr_schedulestatus: "Scheduled",
          carr_assigneddock: "Dock 1",
        },
        {
          carr_trailerid: "CARR-014",
          carr_factorysupplier: "Factory N",
          carr_otifscore: 4,
          carr_revenueimpact: 47000,
          carr_compositescore: 20.6,
          carr_priorityrank: 14,
          carr_schedulestatus: "Unscheduled",
          carr_assigneddock: "",
        },
        {
          carr_trailerid: "CARR-015",
          carr_factorysupplier: "Factory O",
          carr_otifscore: 5,
          carr_revenueimpact: 76000,
          carr_compositescore: 27.2,
          carr_priorityrank: 15,
          carr_schedulestatus: "Confirmed",
          carr_assigneddock: "Dock 2",
        },
        {
          carr_trailerid: "CARR-016",
          carr_factorysupplier: "Factory P",
          carr_otifscore: 3,
          carr_revenueimpact: 22000,
          carr_compositescore: 14.6,
          carr_priorityrank: 16,
          carr_schedulestatus: "Unscheduled",
          carr_assigneddock: "",
        },
      ];
    },
  });
}

// ─── Trailer Dashboard Page ───────────────────────────────────────────────────
function TrailerDashboard() {
  const styles = useStyles();
  const navigate = useNavigate();
  const { data: trailers = [], isLoading, refetch } = useTrailers();
  const [scenario, setScenario] = useState<ScenarioSettings>(DEFAULT_SCENARIO);
  const [selectedTrailerId, setSelectedTrailerId] = useState<string>("");

  const simulatedTrailers = buildSimulation(trailers, scenario);
  const selectedTrailer = simulatedTrailers.find((t) => t.carr_trailerid === selectedTrailerId) ?? simulatedTrailers[0];
  const impactMetrics = buildImpactMetrics(trailers, simulatedTrailers, scenario);
  const dispatchPlan = buildDispatchPlan(simulatedTrailers, scenario);
  const exceptions = buildExceptions(simulatedTrailers, scenario);

  const totalRevenue = trailers.reduce((sum, t) => sum + (t.carr_revenueimpact ?? 0), 0);
  const scheduled = trailers.filter((t) => isScheduled(t.carr_schedulestatus)).length;
  const unscheduled = trailers.filter((t) => t.carr_schedulestatus === "Unscheduled").length;

  function updateScenario<K extends keyof ScenarioSettings>(key: K, value: ScenarioSettings[K]) {
    setScenario((prev) => ({ ...prev, [key]: value }));
  }

  const columns: TableColumnDefinition<Trailer>[] = [
    createTableColumn<Trailer>({
      columnId: "rank",
      renderHeaderCell: () => "#",
      renderCell: (t) => (
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            backgroundColor: "#004680",
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            fontSize: 13,
          }}
        >
          {t.carr_priorityrank}
        </div>
      ),
    }),
    createTableColumn<Trailer>({
      columnId: "trailerid",
      renderHeaderCell: () => "Trailer ID",
      renderCell: (t) => <Text weight="semibold">{t.carr_trailerid}</Text>,
    }),
    createTableColumn<Trailer>({
      columnId: "supplier",
      renderHeaderCell: () => "Supplier",
      renderCell: (t) => t.carr_factorysupplier,
    }),
    createTableColumn<Trailer>({
      columnId: "otif",
      renderHeaderCell: () => "OTIF",
      renderCell: (t) => <Text style={{ color: "#0078D4", fontWeight: 600 }}>{t.carr_otifscore}</Text>,
    }),
    createTableColumn<Trailer>({
      columnId: "revenue",
      renderHeaderCell: () => "Revenue",
      renderCell: (t) => <Text style={{ color: "#0078D4" }}>${((t.carr_revenueimpact ?? 0) / 1000).toFixed(1)}K</Text>,
    }),
    createTableColumn<Trailer>({
      columnId: "status",
      renderHeaderCell: () => "Status",
      renderCell: (t) => <StatusBadge status={t.carr_schedulestatus} />,
    }),
  ];

  return (
    <div className={styles.page}>
      <div className={styles.contentWrap}>
      <div className={styles.heroGrid}>
        <div className={`${styles.panel} ${styles.scenarioPanel}`}>
          <div className={styles.panelTitleRow}>
            <div>
              <div className={styles.panelTitle}>Scenario Simulator</div>
              <div className={styles.panelSubtitle}>Adjust constraints and see impact</div>
            </div>
            <Button appearance="secondary" onClick={() => setScenario(DEFAULT_SCENARIO)}>
              Reset
            </Button>
          </div>

          <div className={styles.sliderGrid}>
            <div className={styles.sliderCard}>
              <div className={styles.sliderLabelRow}>
                <Text weight="semibold">Late Arrival Risk</Text>
                <Badge appearance="filled">{scenario.lateArrivalRisk}%</Badge>
              </div>
              <Slider
                value={scenario.lateArrivalRisk}
                min={0}
                max={100}
                step={5}
                onChange={(_, data) => updateScenario("lateArrivalRisk", data.value)}
              />
            </div>

            <div className={styles.sliderCard}>
              <div className={styles.sliderLabelRow}>
                <Text weight="semibold">Labor Capacity</Text>
                <Badge appearance="filled">{scenario.laborCapacity}%</Badge>
              </div>
              <Slider
                value={scenario.laborCapacity}
                min={40}
                max={100}
                step={5}
                onChange={(_, data) => updateScenario("laborCapacity", data.value)}
              />
            </div>

            <div className={styles.sliderCard}>
              <div className={styles.sliderLabelRow}>
                <Text weight="semibold">SLA Urgency</Text>
                <Badge appearance="filled">{scenario.slaUrgency}%</Badge>
              </div>
              <Slider
                value={scenario.slaUrgency}
                min={0}
                max={100}
                step={5}
                onChange={(_, data) => updateScenario("slaUrgency", data.value)}
              />
            </div>

            <div className={styles.sliderCard}>
              <div className={styles.sliderLabelRow}>
                <Text weight="semibold">Dock Availability</Text>
                <Badge appearance="outline">{scenario.dockOutage ? "Dock 1 down" : "All docks"}</Badge>
              </div>
              <Checkbox
                label="Simulate Dock 1 outage"
                checked={scenario.dockOutage}
                onChange={(_, data) => updateScenario("dockOutage", !!data.checked)}
              />
            </div>
          </div>

          <div className={styles.summaryBand}>
            <div className={styles.summaryChip}>Capacity: {scenarioCapacity(scenario)} trailers/4hrs</div>
            <div className={styles.summaryChip}>Top move: {dispatchPlan[0]?.trailerId}</div>
            <div className={styles.summaryChip}>Exceptions: {exceptions.length}</div>
          </div>
        </div>

        <div className={`${styles.panel} ${styles.focusCard}`}>
          <div className={styles.focusCardTitle}>Focused Trailer</div>
          <div className={styles.focusCardSubtitle}>Select to analyze details</div>
          {selectedTrailer ? (
            <div>
              <div className={styles.focusBadgeRow}>
                <Badge appearance="filled">Rank {selectedTrailer.simulatedRank}</Badge>
                <StatusBadge status={selectedTrailer.carr_schedulestatus} />
              </div>
              <Text weight="semibold">{selectedTrailer.carr_trailerid}</Text>
              <Text size={200}>{selectedTrailer.carr_factorysupplier}</Text>
              <Text size={100} className={styles.focusNote}>
                {selectedTrailer.recommendedAction}
              </Text>
            </div>
          ) : (
            <Text className={styles.focusNote}>Select a trailer</Text>
          )}
        </div>
      </div>

      <div className={styles.kpiRow}>
        <KPICard label="Total Trailers" value={String(trailers.length)} />
        <KPICard label="Scheduled" value={String(scheduled)} color="#107C10" />
        <KPICard label="Unscheduled" value={String(unscheduled)} color="#D13438" />
        <KPICard label="Revenue" value={formatThousands(totalRevenue)} />
      </div>

      <div className={styles.kpiRow}>
        <KPICard
          label="Detention Avoided"
          value={formatThousands(impactMetrics.detentionAvoided)}
          delta="Potential value"
          color="#004680"
        />
        <KPICard
          label="SLA Breaches Prevented"
          value={String(impactMetrics.breachesPrevented)}
          delta={formatDelta(impactMetrics.breachesPrevented)}
          color="#107C10"
        />
        <KPICard
          label="Dock Utilization"
          value={`${impactMetrics.projectedUtilization}%`}
          delta={formatDelta(impactMetrics.projectedUtilization - impactMetrics.baseUtilization, "%")}
          color="#0b7ad1"
        />
        <KPICard
          label="Queue Reduction"
          value={`${impactMetrics.queueReductionMinutes} min`}
          delta="Next wave"
          color="#8f4bd8"
        />
      </div>

      <div className={`${styles.panel} ${styles.timelinePanel}`}>
        <div className={styles.timelineHeader}>
          <div>
            <div className={styles.timelineTitle}>Dock Timeline</div>
            <div className={styles.timelineSubtitle}>
              4-hour dispatch plan across all docks, visualizing throughput and conflicts.
            </div>
          </div>
        </div>

        <div className={styles.timelineGrid}>
          <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end" }} />
          <div className={styles.timelineHours}>
            {PLAN_WINDOWS.map((window) => (
              <div key={window} className={styles.timeHour}>
                {window}
              </div>
            ))}
          </div>

          {["Dock 1", "Dock 2", "Overflow"].map((dockName) => (
            <div key={dockName} className={styles.dockLabel}>
              {dockName}
            </div>
          ))}

          {["Dock 1", "Dock 2", "Overflow"].map((dockName) => {
            const dockTrailers = dispatchPlan.filter((stop) => stop.dock === dockName);
            const bucketedByWindow = PLAN_WINDOWS.map((window) =>
              dockTrailers.filter((stop) => stop.window === window)
            );

            return (
              <div key={`lane-${dockName}`} className={styles.dockLane}>
                {bucketedByWindow.map((bucketed, idx) => (
                  <div key={`bucket-${idx}`} className={styles.laneBucket}>
                    {bucketed.map((stop) => {
                      const sim = simulatedTrailers.find((t) => t.carr_trailerid === stop.trailerId);
                      const isHighRank = (sim?.simulatedRank ?? 999) <= 3;
                      const isOverflow = stop.dock === "Overflow";

                      return (
                        <div
                          key={stop.trailerId}
                          className={`${styles.trailerBlock} ${
                            isHighRank
                              ? styles.trailerBlockHighRank
                              : isOverflow
                              ? styles.trailerBlockOverflow
                              : ""
                          }`}
                          title={`${stop.trailerId} - ${stop.supplier}`}
                        >
                          {stop.trailerId}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            );
          })}
        </div>

        <div className={styles.footerNote}>
          Darker blue = top 3 priority, Orange = overflow, showing 4-hour dispatch flow.
        </div>
      </div>

      <div className={styles.contentGrid}>
        <div className={`${styles.panel} ${styles.tablePanel}`}>
          <div className={styles.toolbar}>
            <Button icon={<ArrowSync24Regular />} onClick={() => refetch()} disabled={isLoading}>
              Refresh
            </Button>
            <Button icon={<Calendar24Regular />} appearance="primary" onClick={() => navigate("/schedule")}>
              Open Schedule Builder
            </Button>
            {isLoading && <Spinner size="tiny" label="Loading..." />}
          </div>

          {isLoading ? (
            <div style={{ padding: 48, textAlign: "center" }}>
              <Spinner size="large" label="Loading trailers..." />
            </div>
          ) : (
            <div className={styles.tableWrap}>
              <DataGrid items={simulatedTrailers} columns={columns} sortable resizableColumns>
                <DataGridHeader>
                  <DataGridRow>
                    {({ renderHeaderCell }) => <DataGridHeaderCell>{renderHeaderCell()}</DataGridHeaderCell>}
                  </DataGridRow>
                </DataGridHeader>
                <DataGridBody<Trailer>>
                  {({ item, rowId }) => (
                    <DataGridRow<Trailer>
                      key={rowId}
                      onClick={() => setSelectedTrailerId(item.carr_trailerid)}
                    >
                      {({ renderCell }) => <DataGridCell>{renderCell(item)}</DataGridCell>}
                    </DataGridRow>
                  )}
                </DataGridBody>
              </DataGrid>
            </div>
          )}
        </div>

        <div className={`${styles.panel} ${styles.exceptionPanel}`}>
          <div className={styles.panelTitle}>Exceptions</div>
          <div className={styles.panelSubtitle}>Items requiring immediate action</div>
          {exceptions.length > 0 ? (
            <div className={styles.exceptionList}>
              {exceptions.map((ex, idx) => (
                <div key={idx} className={styles.exceptionItem}>
                  <div className={styles.focusBadgeRow}>
                    <Badge appearance="outline">{ex.type}</Badge>
                  </div>
                  <Text weight="semibold">{ex.trailer.carr_trailerid}</Text>
                  <Text size={200}>{ex.trailer.carr_factorysupplier}</Text>
                  <Text size={200} className={styles.focusNote}>
                    Recommended: {ex.trailer.recommendedAction}
                  </Text>
                </div>
              ))}
            </div>
          ) : (
            <Text className={styles.focusNote}>No exceptions detected</Text>
          )}
        </div>
      </div>
      </div>
    </div>
  );
}

// ─── App shell ────────────────────────────────────────────────────────────────
export default function App() {
  const styles = useStyles();
  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <VehicleTruckProfile24Regular style={{ color: "white" }} />
            <div className={styles.headerText}>
              <span className={styles.headerEyebrow}>Operations Command Center</span>
              <span className={styles.headerTitle}>Carrier Inbound Trailer Prioritization</span>
              <span className={styles.headerSubtitle}>Scenario-driven dock planning and exception control</span>
            </div>
          </div>
          <div className={styles.headerPillRow}>
            <span className={styles.headerPill}>Phase 1 Ready</span>
            <span className={styles.headerPill}>Live Simulator</span>
            <span className={styles.headerPill}>Dispatch View</span>
          </div>
        </div>
      </header>
      <TrailerDashboard />
    </div>
  );
}
