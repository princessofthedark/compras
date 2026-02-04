import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid, Card, CardContent, CardActionArea, Typography, Box, CircularProgress,
  Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Button, Divider,
} from '@mui/material';
import {
  ShoppingCart, HourglassEmpty, CheckCircle, TrendingUp,
  Warning, AttachMoney, Add, Assessment,
} from '@mui/icons-material';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const STATUS_COLORS = {
  BORRADOR: 'default', PENDIENTE_GERENTE: 'warning',
  APROBADA_POR_GERENTE: 'info', APROBADA: 'success',
  RECHAZADA_GERENTE: 'error', RECHAZADA_FINANZAS: 'error',
  EN_PROCESO: 'primary', COMPRADA: 'secondary',
  COMPLETADA: 'success', CANCELADA: 'default',
};

const STATUS_LABELS = {
  BORRADOR: 'Borrador', PENDIENTE_GERENTE: 'Pend. Gerente',
  APROBADA_POR_GERENTE: 'Aprob. Gerente', APROBADA: 'Aprobada',
  RECHAZADA_GERENTE: 'Rech. Gerente', RECHAZADA_FINANZAS: 'Rech. Finanzas',
  EN_PROCESO: 'En Proceso', COMPRADA: 'Comprada',
  COMPLETADA: 'Completada', CANCELADA: 'Cancelada',
};

function StatCard({ title, value, icon, color = 'primary.main', onClick }) {
  const content = (
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography color="text.secondary" variant="body2">{title}</Typography>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>{value}</Typography>
        </Box>
        <Box sx={{ color, fontSize: 48 }}>{icon}</Box>
      </Box>
    </CardContent>
  );

  return (
    <Card>
      {onClick ? <CardActionArea onClick={onClick}>{content}</CardActionArea> : content}
    </Card>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [recentRequests, setRecentRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.get('/reports/dashboard/'),
      api.get('/requests/purchase-requests/', { params: { page_size: 5 } }),
    ])
      .then(([dashRes, reqRes]) => {
        setData(dashRes.data);
        setRecentRequests(reqRes.data.results || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="contained" startIcon={<Add />} size="small"
            onClick={() => navigate('/solicitudes')}>
            Nueva Solicitud
          </Button>
          <Button variant="outlined" startIcon={<Assessment />} size="small"
            onClick={() => navigate('/reportes')}>
            Reportes
          </Button>
        </Box>
      </Box>

      {/* Stat Cards */}
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Pendientes Gerente" value={data?.pending_manager_approval || 0}
            icon={<HourglassEmpty fontSize="inherit" />} color="warning.main"
            onClick={() => navigate('/solicitudes')} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Pendientes Finanzas" value={data?.pending_finance_approval || 0}
            icon={<ShoppingCart fontSize="inherit" />} color="info.main"
            onClick={() => navigate('/solicitudes')} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="En Proceso" value={data?.in_process || 0}
            icon={<TrendingUp fontSize="inherit" />} color="primary.main"
            onClick={() => navigate('/solicitudes')} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Completadas (mes)" value={data?.completed_this_month || 0}
            icon={<CheckCircle fontSize="inherit" />} color="success.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Gasto del Mes" value={`$${Number(data?.monthly_spend || 0).toLocaleString()}`}
            icon={<AttachMoney fontSize="inherit" />} color="secondary.main"
            onClick={() => navigate('/presupuestos')} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard title="Exceden Presupuesto" value={data?.exceeding_budget || 0}
            icon={<Warning fontSize="inherit" />} color="error.main"
            onClick={() => navigate('/presupuestos')} />
        </Grid>
      </Grid>

      {/* Recent Requests */}
      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>Solicitudes Recientes</Typography>
          <Button size="small" onClick={() => navigate('/solicitudes')}>Ver todas</Button>
        </Box>
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>No. Solicitud</TableCell>
                <TableCell>Descripcion</TableCell>
                <TableCell>Monto</TableCell>
                <TableCell>Estado</TableCell>
                <TableCell>Fecha</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recentRequests.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">No hay solicitudes recientes</TableCell>
                </TableRow>
              ) : recentRequests.map((r) => (
                <TableRow key={r.id} hover sx={{ cursor: 'pointer' }}
                  onClick={() => navigate('/solicitudes')}>
                  <TableCell sx={{ fontWeight: 600 }}>{r.request_number}</TableCell>
                  <TableCell>{r.description?.substring(0, 40)}</TableCell>
                  <TableCell>${Number(r.estimated_amount).toLocaleString()}</TableCell>
                  <TableCell>
                    <Chip label={STATUS_LABELS[r.status] || r.status}
                      color={STATUS_COLORS[r.status] || 'default'} size="small" />
                  </TableCell>
                  <TableCell>{new Date(r.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
}
