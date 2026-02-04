import { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper, Chip, CircularProgress, TablePagination, TextField,
  MenuItem, Grid, InputAdornment, Button,
} from '@mui/material';
import { Search, FilterList, EventBusy } from '@mui/icons-material';
import api from '../api/client';

const ROLE_LABELS = {
  EMPLEADO: 'Empleado', GERENTE: 'Gerente',
  FINANZAS: 'Finanzas', DIRECCION_GENERAL: 'Direccion General',
};
const ROLE_COLORS = {
  EMPLEADO: 'default', GERENTE: 'primary',
  FINANZAS: 'success', DIRECCION_GENERAL: 'error',
};

export default function Usuarios() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [count, setCount] = useState(0);
  const [searchText, setSearchText] = useState('');
  const [searchDebounced, setSearchDebounced] = useState('');
  const [filterRole, setFilterRole] = useState('');

  useEffect(() => {
    const t = setTimeout(() => setSearchDebounced(searchText), 400);
    return () => clearTimeout(t);
  }, [searchText]);

  useEffect(() => { setPage(0); }, [searchDebounced, filterRole]);

  const fetchUsers = useCallback(() => {
    setLoading(true);
    const params = { page: page + 1 };
    if (searchDebounced) params.search = searchDebounced;
    if (filterRole) params.role = filterRole;
    api.get('/users/users/', { params })
      .then(({ data }) => { setUsers(data.results); setCount(data.count); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page, searchDebounced, filterRole]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Usuarios</Typography>

      {/* Filter Bar */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={5}>
            <TextField
              fullWidth size="small" placeholder="Buscar por nombre, email..."
              value={searchText} onChange={(e) => setSearchText(e.target.value)}
              InputProps={{
                startAdornment: <InputAdornment position="start"><Search /></InputAdornment>,
              }}
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField select fullWidth size="small" label="Rol" value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}>
              <MenuItem value="">Todos</MenuItem>
              {Object.entries(ROLE_LABELS).map(([k, v]) => (
                <MenuItem key={k} value={k}>{v}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={6} sm={4}>
            {(filterRole || searchText) && (
              <Button size="small" startIcon={<FilterList />} onClick={() => {
                setFilterRole(''); setSearchText('');
              }}>
                Limpiar filtros
              </Button>
            )}
            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
              {count} usuario{count !== 1 ? 's' : ''}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Rol</TableCell>
              <TableCell>Area</TableCell>
              <TableCell>Ubicacion</TableCell>
              <TableCell>Estado</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={6} align="center"><CircularProgress /></TableCell></TableRow>
            ) : users.length === 0 ? (
              <TableRow><TableCell colSpan={6} align="center">No hay usuarios</TableCell></TableRow>
            ) : users.map((u) => (
              <TableRow key={u.id} hover>
                <TableCell>{u.first_name} {u.last_name}</TableCell>
                <TableCell>{u.email}</TableCell>
                <TableCell>
                  <Chip label={ROLE_LABELS[u.role] || u.role} color={ROLE_COLORS[u.role] || 'default'} size="small" />
                </TableCell>
                <TableCell>{u.area_name}</TableCell>
                <TableCell>{u.location_name}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Chip label={u.is_active ? 'Activo' : 'Inactivo'}
                      color={u.is_active ? 'success' : 'default'} size="small" />
                    {u.is_out_of_office && (
                      <Chip icon={<EventBusy />} label="OOO" color="warning" size="small" variant="outlined" />
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination component="div" count={count} page={page}
          onPageChange={(_, p) => setPage(p)} rowsPerPage={20} rowsPerPageOptions={[20]} />
      </TableContainer>
    </Box>
  );
}
