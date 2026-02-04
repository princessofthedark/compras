import { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper, Button, TextField, MenuItem, Chip, CircularProgress,
  LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Alert,
  Grid, Card, CardContent,
} from '@mui/material';
import { Lock, LockOpen, AccountBalance, Warning, TrendingUp } from '@mui/icons-material';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Presupuestos() {
  const { user } = useAuth();
  const [budgets, setBudgets] = useState([]);
  const [costCenters, setCostCenters] = useState([]);
  const [loading, setLoading] = useState(true);
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [filterCC, setFilterCC] = useState('');
  const [openCopy, setOpenCopy] = useState(false);
  const [copyForm, setCopyForm] = useState({ target_year: now.getFullYear(), target_month: '' });
  const [message, setMessage] = useState('');

  const canManage = user?.role === 'FINANZAS' || user?.role === 'DIRECCION_GENERAL';

  useEffect(() => {
    api.get('/users/cost-centers/', { params: { page_size: 100 } })
      .then(({ data }) => setCostCenters(data.results || []));
  }, []);

  const fetchBudgets = useCallback(() => {
    setLoading(true);
    const params = { year, month };
    if (filterCC) params.cost_center = filterCC;
    api.get('/budgets/budgets/', { params })
      .then(({ data }) => setBudgets(data.results || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [year, month, filterCC]);

  useEffect(() => { fetchBudgets(); }, [fetchBudgets]);

  const handleCloseMonth = async () => {
    if (!confirm(`Cerrar presupuestos de ${year}/${String(month).padStart(2, '0')}?`)) return;
    try {
      const { data } = await api.post('/budgets/budgets/close_month/', { year, month });
      setMessage(data.message);
      fetchBudgets();
    } catch (err) {
      alert(err.response?.data?.error || 'Error');
    }
  };

  const handleReopenMonth = async () => {
    try {
      const { data } = await api.post('/budgets/budgets/reopen_month/', { year, month });
      setMessage(data.message);
      fetchBudgets();
    } catch (err) {
      alert(err.response?.data?.error || 'Error');
    }
  };

  const handleCopyMonth = async () => {
    try {
      const { data } = await api.post('/budgets/budgets/copy_month/', {
        source_year: year, source_month: month, ...copyForm,
      });
      setMessage(data.message);
      setOpenCopy(false);
    } catch (err) {
      alert(err.response?.data?.error || 'Error');
    }
  };

  const months = [
    { v: 1, l: 'Enero' }, { v: 2, l: 'Febrero' }, { v: 3, l: 'Marzo' },
    { v: 4, l: 'Abril' }, { v: 5, l: 'Mayo' }, { v: 6, l: 'Junio' },
    { v: 7, l: 'Julio' }, { v: 8, l: 'Agosto' }, { v: 9, l: 'Septiembre' },
    { v: 10, l: 'Octubre' }, { v: 11, l: 'Noviembre' }, { v: 12, l: 'Diciembre' },
  ];

  const anyOpen = budgets.some(b => !b.is_closed);
  const anyClosed = budgets.some(b => b.is_closed);

  // Summary calculations
  const totalBudgeted = budgets.reduce((s, b) => s + Number(b.amount || 0), 0);
  const totalSpent = budgets.reduce((s, b) => s + Number(b.spent_amount || 0), 0);
  const totalAvailable = totalBudgeted - totalSpent;
  const exceededCount = budgets.filter(b => b.is_exceeded).length;

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Presupuestos</Typography>

      {message && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage('')}>{message}</Alert>}

      {/* Summary Cards */}
      {!loading && budgets.length > 0 && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="caption" color="text.secondary">Presupuestado</Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  ${totalBudgeted.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="caption" color="text.secondary">Gastado</Typography>
                <Typography variant="h6" sx={{ fontWeight: 700, color: 'warning.main' }}>
                  ${totalSpent.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="caption" color="text.secondary">Disponible</Typography>
                <Typography variant="h6" sx={{ fontWeight: 700, color: totalAvailable < 0 ? 'error.main' : 'success.main' }}>
                  ${totalAvailable.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="caption" color="text.secondary">Excedidos</Typography>
                <Typography variant="h6" sx={{ fontWeight: 700, color: exceededCount > 0 ? 'error.main' : 'text.primary' }}>
                  {exceededCount} / {budgets.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Grid container spacing={2} sx={{ mb: 3 }} alignItems="center">
        <Grid item>
          <TextField select label="Anio" value={year} onChange={(e) => setYear(e.target.value)}
            size="small" sx={{ width: 120 }}>
            {[2024, 2025, 2026, 2027].map(y => <MenuItem key={y} value={y}>{y}</MenuItem>)}
          </TextField>
        </Grid>
        <Grid item>
          <TextField select label="Mes" value={month} onChange={(e) => setMonth(e.target.value)}
            size="small" sx={{ width: 150 }}>
            {months.map(m => <MenuItem key={m.v} value={m.v}>{m.l}</MenuItem>)}
          </TextField>
        </Grid>
        <Grid item>
          <TextField select label="Centro de Costos" value={filterCC}
            onChange={(e) => setFilterCC(e.target.value)}
            size="small" sx={{ width: 200 }}>
            <MenuItem value="">Todos</MenuItem>
            {costCenters.map(cc => (
              <MenuItem key={cc.id} value={cc.id}>{cc.code} - {cc.name}</MenuItem>
            ))}
          </TextField>
        </Grid>
        {canManage && (
          <>
            <Grid item>
              <Button variant="outlined" size="small" onClick={() => setOpenCopy(true)}>
                Copiar Mes
              </Button>
            </Grid>
            <Grid item>
              {anyOpen && (
                <Button variant="outlined" color="warning" size="small" startIcon={<Lock />}
                  onClick={handleCloseMonth}>Cerrar Mes</Button>
              )}
            </Grid>
            <Grid item>
              {anyClosed && (
                <Button variant="outlined" color="success" size="small" startIcon={<LockOpen />}
                  onClick={handleReopenMonth}>Reabrir Mes</Button>
              )}
            </Grid>
          </>
        )}
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Centro de Costos</TableCell>
              <TableCell>Categoria</TableCell>
              <TableCell align="right">Presupuesto</TableCell>
              <TableCell align="right">Gastado</TableCell>
              <TableCell align="right">Disponible</TableCell>
              <TableCell>Utilizacion</TableCell>
              <TableCell>Estado</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={7} align="center"><CircularProgress /></TableCell></TableRow>
            ) : budgets.length === 0 ? (
              <TableRow><TableCell colSpan={7} align="center">No hay presupuestos para este periodo</TableCell></TableRow>
            ) : budgets.map((b) => {
              const pct = b.utilization_percentage || 0;
              const color = pct > 100 ? 'error' : pct > 80 ? 'warning' : 'success';
              return (
                <TableRow key={b.id} hover>
                  <TableCell>{b.cost_center_name}</TableCell>
                  <TableCell>{b.category_name}</TableCell>
                  <TableCell align="right">${Number(b.amount).toLocaleString()}</TableCell>
                  <TableCell align="right">${Number(b.spent_amount).toLocaleString()}</TableCell>
                  <TableCell align="right" sx={{ color: b.is_exceeded ? 'error.main' : 'inherit', fontWeight: b.is_exceeded ? 700 : 400 }}>
                    ${Number(b.available_amount).toLocaleString()}
                  </TableCell>
                  <TableCell sx={{ minWidth: 150 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress variant="determinate" value={Math.min(pct, 100)}
                        color={color} sx={{ flexGrow: 1, height: 8, borderRadius: 4 }} />
                      <Typography variant="caption">{pct}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {b.is_closed ? (
                      <Chip label="Cerrado" size="small" icon={<Lock />} color="default" />
                    ) : b.is_exceeded ? (
                      <Chip label="Excedido" size="small" color="error" />
                    ) : (
                      <Chip label="Abierto" size="small" color="success" />
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog Copiar Mes */}
      <Dialog open={openCopy} onClose={() => setOpenCopy(false)}>
        <DialogTitle>Copiar Presupuestos</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Copiar presupuestos de {months.find(m => m.v === month)?.l} {year} a:
          </Typography>
          <TextField select fullWidth label="Anio destino" margin="normal" value={copyForm.target_year}
            onChange={(e) => setCopyForm({ ...copyForm, target_year: e.target.value })}>
            {[2024, 2025, 2026, 2027].map(y => <MenuItem key={y} value={y}>{y}</MenuItem>)}
          </TextField>
          <TextField select fullWidth label="Mes destino" margin="normal" value={copyForm.target_month}
            onChange={(e) => setCopyForm({ ...copyForm, target_month: e.target.value })}>
            {months.map(m => <MenuItem key={m.v} value={m.v}>{m.l}</MenuItem>)}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCopy(false)}>Cancelar</Button>
          <Button variant="contained" onClick={handleCopyMonth}>Copiar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
