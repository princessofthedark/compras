import { useState, useEffect } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper, Chip, CircularProgress, TablePagination,
} from '@mui/material';
import api from '../api/client';

const ROLE_LABELS = {
  EMPLEADO: 'Empleado', GERENTE: 'Gerente',
  FINANZAS: 'Finanzas', DIRECCION_GENERAL: 'Dirección General',
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

  useEffect(() => {
    setLoading(true);
    api.get('/users/users/', { params: { page: page + 1 } })
      .then(({ data }) => { setUsers(data.results); setCount(data.count); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Usuarios</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Rol</TableCell>
              <TableCell>Área</TableCell>
              <TableCell>Ubicación</TableCell>
              <TableCell>Estado</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={6} align="center"><CircularProgress /></TableCell></TableRow>
            ) : users.map((u) => (
              <TableRow key={u.id}>
                <TableCell>{u.first_name} {u.last_name}</TableCell>
                <TableCell>{u.email}</TableCell>
                <TableCell>
                  <Chip label={ROLE_LABELS[u.role]} color={ROLE_COLORS[u.role]} size="small" />
                </TableCell>
                <TableCell>{u.area_name}</TableCell>
                <TableCell>{u.location_name}</TableCell>
                <TableCell>
                  <Chip label={u.is_active ? 'Activo' : 'Inactivo'}
                    color={u.is_active ? 'success' : 'default'} size="small" />
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
