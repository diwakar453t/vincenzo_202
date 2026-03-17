import { FormEvent, useEffect, useState } from "react";
import { Alert, Box, Button, Card, CardContent, CircularProgress, Grid, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import { createResource, deleteResource, fetchResource } from "../store/slices/resourcesSlice";
import type { AppDispatch, RootState } from "../store/store";

export default function ResourcePage({ resource, title, fields }: { resource: string; title: string; fields: string[] }) {
  const dispatch = useDispatch<AppDispatch>();
  const items = useSelector((state: RootState) => state.resources.byResource[resource] as Record<string, unknown>[] | undefined) ?? [];
  const [form, setForm] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void dispatch(fetchResource(resource));
  }, [dispatch, resource]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    const payload = Object.fromEntries(
      Object.entries(form)
        .map(([key, value]) => [key, value.trim() === "" ? undefined : value])
        .filter(([, value]) => value !== undefined)
    );
    await dispatch(createResource({ resource, payload }));
    setForm({});
    setLoading(false);
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4" sx={{ fontWeight: 700 }}>{title}</Typography>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ borderRadius: 3, boxShadow: "0 20px 45px rgba(15, 23, 42, 0.08)" }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Add {title.slice(0, -1)}</Typography>
              <Box component="form" onSubmit={handleSubmit}>
                <Stack spacing={2}>
                  {fields.map((field) => (
                    <TextField
                      key={field}
                      label={field.replaceAll("_", " ")}
                      value={form[field] ?? ""}
                      onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))}
                      fullWidth
                      size="small"
                    />
                  ))}
                  <Button type="submit" variant="contained" disabled={loading}>
                    {loading ? <CircularProgress size={18} color="inherit" /> : "Save"}
                  </Button>
                </Stack>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 8 }}>
          <Card sx={{ borderRadius: 3, boxShadow: "0 20px 45px rgba(15, 23, 42, 0.08)" }}>
            <CardContent>
              {items.length === 0 ? (
                <Alert severity="info">No records found</Alert>
              ) : (
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      {fields.map((field) => <TableCell key={field}>{field}</TableCell>)}
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((item, index) => (
                      <TableRow key={String(item.id ?? index)} sx={{ "&:nth-of-type(odd)": { bgcolor: "rgba(61,94,225,0.03)" } }}>
                        {fields.map((field) => <TableCell key={field}>{String(item[field] ?? "")}</TableCell>)}
                        <TableCell align="right">
                          <Button color="error" onClick={() => void dispatch(deleteResource({ resource, id: Number(item.id) }))}>Delete</Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}
