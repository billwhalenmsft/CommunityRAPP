import { PowerAppsClient } from "@microsoft/power-apps";
import {
  FluentProvider,
  webLightTheme,
  makeStyles,
  tokens,
  Text,
  Badge,
  Button,
  Spinner,
  DataGrid,
  DataGridHeader,
  DataGridHeaderCell,
  DataGridBody,
  DataGridRow,
  DataGridCell,
  TableColumnDefinition,
  createTableColumn,
} from "@fluentui/react-components";
import {
  ArrowSync24Regular,
  Calendar24Regular,
  VehicleTruckProfile24Regular,
} from "@fluentui/react-icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";

// ─── Power Apps Dataverse client ───────────────────────────────────────────
const client = new PowerAppsClient();

interface Trailer {
  carr_trailerid: string;
  carr_factorysupplier: string;
  carr_shipdate: string;
  carr_otifscore: number;
  carr_revenueimpact: number;
  carr_compositescore: number;
  carr_priorityrank: number;
  carr_schedulestatus: string;
  carr_assigneddock: string;
  carr_scheduleddate?: string;
  carr_approvedoverflow: boolean;
}

// ─── Data hooks ─────────────────────────────────────────────────────────────
function useTrailers() {
  return useQuery<Trailer[]>({
    queryKey: ["trailers"],
    queryFn: async () => {
      const result = await client.retrieve("carr_trailers", {
        select: [
          "carr_trailerid",
          "carr_factorysupplier",
          "carr_shipdate",
          "carr_otifscore",
          "carr_revenueimpact",
          "carr_compositescore",
          "carr_priorityrank",
          "carr_schedulestatus",
          "carr_assigneddock",
          "carr_scheduleddate",
          "carr_approvedoverflow",
        ],
        orderby: "carr_priorityrank asc",
      });
      return result.value;
    },
    refetchInterval: 60_000, // auto-refresh every minute
  });
}

function useAssignDock() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      dock,
      date,
    }: {
      id: string;
      dock: string;
      date: string;
    }) => {
      await client.update("carr_trailers", id, {
        carr_assigneddock: dock,
        carr_scheduleddate: date,
        carr_schedulestatus: "Scheduled",
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["trailers"] }),
  });
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const useStyles = makeStyles({
  app: {
    minHeight: "100vh",
    backgroundColor: tokens.colorNeutralBackground2,
  },
  header: {
    backgroundColor: "#004680",
    padding: "0 24px",
    height: "64px",
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  headerTitle: {
    color: "white",
    fontSize: "18px",
    fontWeight: "600",
  },
  kpiRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "16px",
    padding: "16px 24px",
  },
  kpiCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: "8px",
    padding: "16px",
    border: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  kpiNumber: {
    fontSize: "32px",
    fontWeight: "700",
    lineHeight: "1",
    marginBottom: "4px",
  },
  tableContainer: {
    margin: "0 24px",
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: "8px",
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    overflow: "hidden",
  },
  toolbar: {
    padding: "12px 24px",
    display: "flex",
    gap: "12px",
    alignItems: "center",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  statusBadge: {
    textTransform: "capitalize",
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
  color,
}: {
  label: string;
  value: string;
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
    </div>
  );
}

// ─── Trailer Dashboard Page ───────────────────────────────────────────────────
function TrailerDashboard() {
  const styles = useStyles();
  const navigate = useNavigate();
  const { data: trailers = [], isLoading, refetch } = useTrailers();
  const assignDock = useAssignDock();

  const totalRevenue = trailers.reduce((s, t) => s + (t.carr_revenueimpact ?? 0), 0);
  const scheduled = trailers.filter(
    (t) => t.carr_schedulestatus === "Scheduled" || t.carr_schedulestatus === "Confirmed"
  ).length;
  const unscheduled = trailers.filter((t) => t.carr_schedulestatus === "Unscheduled").length;

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
      renderHeaderCell: () => "Supplier / Factory",
      renderCell: (t) => t.carr_factorysupplier,
    }),
    createTableColumn<Trailer>({
      columnId: "otif",
      renderHeaderCell: () => "OTIF Parts",
      renderCell: (t) => (
        <Text style={{ color: "#0078D4", fontWeight: 600 }}>
          {t.carr_otifscore ?? 0}
        </Text>
      ),
    }),
    createTableColumn<Trailer>({
      columnId: "revenue",
      renderHeaderCell: () => "Revenue Impact",
      renderCell: (t) => (
        <Text style={{ color: "#0078D4" }}>
          ${((t.carr_revenueimpact ?? 0) / 1000).toFixed(1)}K
        </Text>
      ),
    }),
    createTableColumn<Trailer>({
      columnId: "score",
      renderHeaderCell: () => "Score",
      renderCell: (t) => (
        <Text weight="semibold">{(t.carr_compositescore ?? 0).toFixed(2)}</Text>
      ),
    }),
    createTableColumn<Trailer>({
      columnId: "status",
      renderHeaderCell: () => "Status",
      renderCell: (t) => <StatusBadge status={t.carr_schedulestatus} />,
    }),
    createTableColumn<Trailer>({
      columnId: "dock",
      renderHeaderCell: () => "Dock",
      renderCell: (t) =>
        t.carr_assigneddock !== "Unassigned" ? (
          <Badge appearance="outline">{t.carr_assigneddock}</Badge>
        ) : (
          <Text style={{ color: tokens.colorNeutralForeground3 }}>—</Text>
        ),
    }),
    createTableColumn<Trailer>({
      columnId: "actions",
      renderHeaderCell: () => "",
      renderCell: (t) =>
        t.carr_schedulestatus === "Unscheduled" ? (
          <Button
            size="small"
            appearance="primary"
            onClick={() => navigate(`/schedule/${t.carr_trailerid}`)}
          >
            Assign
          </Button>
        ) : null,
    }),
  ];

  return (
    <div>
      <div className={styles.kpiRow}>
        <KPICard label="Total Trailers" value={String(trailers.length)} />
        <KPICard
          label="Scheduled"
          value={String(scheduled)}
          color="#107C10"
        />
        <KPICard
          label="Unscheduled"
          value={String(unscheduled)}
          color="#D13438"
        />
        <KPICard
          label="Potential Revenue"
          value={`$${(totalRevenue / 1000).toFixed(0)}K`}
          color="#0078D4"
        />
      </div>

      <div className={styles.tableContainer}>
        <div className={styles.toolbar}>
          <Button
            icon={<ArrowSync24Regular />}
            onClick={() => refetch()}
            disabled={isLoading}
          >
            Refresh
          </Button>
          <Button
            icon={<Calendar24Regular />}
            appearance="primary"
            onClick={() => navigate("/schedule")}
          >
            Open Schedule Builder
          </Button>
          {isLoading && <Spinner size="tiny" label="Loading..." />}
        </div>

        {isLoading ? (
          <div style={{ padding: 48, textAlign: "center" }}>
            <Spinner size="large" label="Loading trailers..." />
          </div>
        ) : (
          <DataGrid items={trailers} columns={columns} sortable resizableColumns>
            <DataGridHeader>
              <DataGridRow>
                {({ renderHeaderCell }) => (
                  <DataGridHeaderCell>{renderHeaderCell()}</DataGridHeaderCell>
                )}
              </DataGridRow>
            </DataGridHeader>
            <DataGridBody<Trailer>>
              {({ item, rowId }) => (
                <DataGridRow<Trailer> key={rowId}>
                  {({ renderCell }) => (
                    <DataGridCell>{renderCell(item)}</DataGridCell>
                  )}
                </DataGridRow>
              )}
            </DataGridBody>
          </DataGrid>
        )}
      </div>
    </div>
  );
}

// ─── App shell ───────────────────────────────────────────────────────────────
function AppShell() {
  const styles = useStyles();
  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <VehicleTruckProfile24Regular style={{ color: "white" }} />
        <span className={styles.headerTitle}>
          Carrier — Inbound Trailer Prioritization
        </span>
      </header>
      <Routes>
        <Route path="/" element={<TrailerDashboard />} />
        {/* ScheduleBuilder and Communications pages follow same pattern */}
        <Route path="/schedule" element={<div style={{ padding: 24 }}>Schedule Builder — see canvas-app for full YAML or extend here</div>} />
        <Route path="/comms" element={<div style={{ padding: 24 }}>Communications — Email + TSP contacts</div>} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <FluentProvider theme={webLightTheme}>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </FluentProvider>
  );
}
