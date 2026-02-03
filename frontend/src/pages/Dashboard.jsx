import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid, Card, CardContent, Typography, Box, CircularProgress,
} from '@mui/material';
import {
  ShoppingCart, HourglassEmpty, CheckCircle, TrendingUp,
  Warning, AttachMoney,
} from '@mui/icons-material';
import api from '../api/client';

function StatCard({ title, value, icon, color = 'primary.main' }) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="text.secondary" variant="body2">{title}</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{value}</Typography>
          </Box>
          <Box sx={{ color, fontSize: 48 }}>{icon}</Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/reports/dashboard/')
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Dashboard</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Pendientes Gerente" value={data?.pending_manager_approval || 0}
            icon={<HourglassEmpty fontSize="inherit" />} color="warning.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Pendientes Finanzas" value={data?.pending_finance_approval || 0}
            icon={<ShoppingCart fontSize="inherit" />} color="info.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="En Proceso" value={data?.in_process || 0}
            icon={<TrendingUp fontSize="inherit" />} color="primary.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Completadas (mes)" value={data?.completed_this_month || 0}
            icon={<CheckCircle fontSize="inherit" />} color="success.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Gasto del Mes" value={`$${Number(data?.monthly_spend || 0).toLocaleString()}`}
            icon={<AttachMoney fontSize="inherit" />} color="secondary.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Exceden Presupuesto" value={data?.exceeding_budget || 0}
            icon={<Warning fontSize="inherit" />} color="error.main" />
        </Grid>
      </Grid>
    </Box>
  );
}
