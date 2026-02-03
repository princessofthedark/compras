import { useState } from 'react';
import {
  Box, Typography, Grid, Card, CardContent, CardActions, Button,
  TextField, MenuItem, Alert,
} from '@mui/material';
import { Download, Assessment, CompareArrows, People, Store } from '@mui/icons-material';
import api from '../api/client';

const REPORTS = [
  { key: 'expenses-by-period', title: 'Gastos por Periodo',
    icon: <Assessment sx={{ fontSize: 48 }} />, desc: 'Reporte de gastos agrupados por categoría y centro de costos.',
    formats: ['excel', 'pdf'] },
  { key: 'budget-comparison', title: 'Comparativo Presupuestal',
    icon: <CompareArrows sx={{ fontSize: 48 }} />, desc: 'Presupuesto vs gasto real por categoría y centro de costos.',
    formats: ['excel', 'pdf'] },
  { key: 'expenses-by-employee', title: 'Gastos por Empleado',
    icon: <People sx={{ fontSize: 48 }} />, desc: 'Desglose de gastos por cada empleado solicitante.',
    formats: ['excel'] },
  { key: 'top-suppliers', title: 'Proveedores Principales',
    icon: <Store sx={{ fontSize: 48 }} />, desc: 'Top proveedores por monto y cantidad de compras.',
    formats: ['excel'] },
];

export default function Reportes() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState('');
  const [downloading, setDownloading] = useState('');
  const [error, setError] = useState('');

  const months = [
    { v: '', l: 'Todos' }, { v: 1, l: 'Enero' }, { v: 2, l: 'Febrero' },
    { v: 3, l: 'Marzo' }, { v: 4, l: 'Abril' }, { v: 5, l: 'Mayo' },
    { v: 6, l: 'Junio' }, { v: 7, l: 'Julio' }, { v: 8, l: 'Agosto' },
    { v: 9, l: 'Septiembre' }, { v: 10, l: 'Octubre' }, { v: 11, l: 'Noviembre' },
    { v: 12, l: 'Diciembre' },
  ];

  const downloadReport = async (reportKey, format) => {
    setDownloading(`${reportKey}-${format}`);
    setError('');
    try {
      const params = { year, export: format };
      if (month) params.month = month;
      const response = await api.get(`/reports/${reportKey}/`, {
        params,
        responseType: 'blob',
      });
      const ext = format === 'pdf' ? 'pdf' : 'xlsx';
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${reportKey}_${year}${month ? '_' + month : ''}.${ext}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError(`Error al descargar ${reportKey}`);
    } finally {
      setDownloading('');
    }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Reportes</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item>
          <TextField select label="Año" value={year} onChange={(e) => setYear(e.target.value)}
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
      </Grid>

      <Grid container spacing={3}>
        {REPORTS.map((r) => (
          <Grid item xs={12} sm={6} md={6} key={r.key}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                  <Box sx={{ color: 'primary.main' }}>{r.icon}</Box>
                  <Typography variant="h6">{r.title}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">{r.desc}</Typography>
              </CardContent>
              <CardActions>
                {r.formats.map(fmt => (
                  <Button key={fmt} size="small" startIcon={<Download />}
                    disabled={downloading === `${r.key}-${fmt}`}
                    onClick={() => downloadReport(r.key, fmt)}>
                    {fmt.toUpperCase()}
                  </Button>
                ))}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
