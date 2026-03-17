import { useEffect } from "react";
import { Alert, Card, CardContent, Grid, Stack, Typography } from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import { fetchDashboardStatistics } from "../store/slices/dashboardSlice";
import type { AppDispatch, RootState } from "../store/store";

const statConfig = [
  ["total_students", "Total Students"],
  ["total_teachers", "Total Teachers"],
  ["active_classes", "Active Classes"],
  ["revenue_this_month", "Revenue This Month"],
  ["attendance_rate", "Attendance Rate"],
  ["fee_collection_rate", "Fee Collection Rate"],
  ["pending_leaves", "Pending Leaves"],
  ["open_issues", "Open Issues"],
];

export default function DashboardPage({ title }: { title: string }) {
  const dispatch = useDispatch<AppDispatch>();
  const stats = useSelector((state: RootState) => state.dashboard.stats);

  useEffect(() => {
    void dispatch(fetchDashboardStatistics());
  }, [dispatch]);

  return (
    <Stack spacing={3}>
      <Typography variant="h4" sx={{ fontWeight: 700 }}>{title}</Typography>
      {!stats ? (
        <Alert severity="info">Loading dashboard data...</Alert>
      ) : (
        <Grid container spacing={3}>
          {statConfig.map(([key, label]) => (
            <Grid size={{ xs: 12, sm: 6, xl: 3 }} key={key}>
              <Card sx={{ borderRadius: 3, minHeight: 140, boxShadow: "0 18px 40px rgba(15,23,42,0.08)", transition: "transform 0.2s ease", "&:hover": { transform: "translateY(-4px)" } }}>
                <CardContent>
                  <Typography color="text.secondary">{label}</Typography>
                  <Typography variant="h4" sx={{ mt: 2, fontWeight: 700 }}>{String(stats[key] ?? 0)}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Stack>
  );
}
