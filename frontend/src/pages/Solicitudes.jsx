import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper, Chip, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem, IconButton, Tooltip, CircularProgress,
  TablePagination, Alert, List, ListItem, ListItemIcon, ListItemText,
  ListItemSecondaryAction, LinearProgress,
} from '@mui/material';
import {
  Add, Visibility, Check, Close, Cancel, AttachFile, Delete,
  PictureAsPdf, CloudUpload,
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

export default function Solicitudes() {
  const { user } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [count, setCount] = useState(0);
  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [openNew, setOpenNew] = useState(false);
  const [openDetail, setOpenDetail] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);
  const [form, setForm] = useState({
    category: '', items: [], description: '', estimated_amount: '',
    required_date: '', justification: '', urgency: 'NORMAL',
  });

  const fetchRequests = useCallback(() => {
    setLoading(true);
    api.get('/requests/purchase-requests/', { params: { page: page + 1 } })
      .then(({ data }) => { setRequests(data.results); setCount(data.count); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page]);

  useEffect(() => { fetchRequests(); }, [fetchRequests]);

  useEffect(() => {
    api.get('/budgets/categories/').then(({ data }) => setCategories(data.results || []));
    api.get('/budgets/items/', { params: { page_size: 300 } }).then(({ data }) => setItems(data.results || []));
  }, []);

  const handleCreate = async () => {
    setError('');
    try {
      await api.post('/requests/purchase-requests/', form);
      setOpenNew(false);
      setForm({ category: '', items: [], description: '', estimated_amount: '',
        required_date: '', justification: '', urgency: 'NORMAL' });
      fetchRequests();
    } catch (err) {
      setError(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Error al crear');
    }
  };

  const handleAction = async (id, action, body = {}) => {
    try {
      await api.post(`/requests/purchase-requests/${id}/${action}/`, body);
      fetchRequests();
      if (selected?.id === id) {
        const { data } = await api.get(`/requests/purchase-requests/${id}/`);
        setSelected(data);
      }
    } catch (err) {
      alert(err.response?.data?.detail || err.response?.data?.error || 'Error');
    }
  };

  const viewDetail = async (id) => {
    const { data } = await api.get(`/requests/purchase-requests/${id}/`);
    setSelected(data);
    setOpenDetail(true);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selected) return;
    setUploadError('');

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Solo se permiten archivos PDF.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('El archivo no puede ser mayor a 10MB.');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('request', selected.id);

    try {
      await api.post('/requests/attachments/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { data } = await api.get(`/requests/purchase-requests/${selected.id}/`);
      setSelected(data);
    } catch (err) {
      const errMsg = err.response?.data?.file?.[0]
        || err.response?.data?.detail
        || JSON.stringify(err.response?.data)
        || 'Error al subir archivo';
      setUploadError(errMsg);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (!window.confirm('Eliminar este archivo adjunto?')) return;
    try {
      await api.delete(`/requests/attachments/${attachmentId}/`);
      const { data } = await api.get(`/requests/purchase-requests/${selected.id}/`);
      setSelected(data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Error al eliminar');
    }
  };

  const filteredItems = items.filter(i => !form.category || i.category === Number(form.category));

  const canApproveManager = user?.role === 'GERENTE';
  const canApproveFinal = user?.role === 'FINANZAS' || user?.role === 'DIRECCION_GENERAL';

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Solicitudes de Compra</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOpenNew(true)}>
          Nueva Solicitud
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>No. Solicitud</TableCell>
              <TableCell>Descripcion</TableCell>
              <TableCell>Monto</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Fecha</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={6} align="center"><CircularProgress /></TableCell></TableRow>
            ) : requests.length === 0 ? (
              <TableRow><TableCell colSpan={6} align="center">No hay solicitudes</TableCell></TableRow>
            ) : requests.map((r) => (
              <TableRow key={r.id}>
                <TableCell sx={{ fontWeight: 600 }}>{r.request_number}</TableCell>
                <TableCell>{r.description?.substring(0, 50)}</TableCell>
                <TableCell>${Number(r.estimated_amount).toLocaleString()}</TableCell>
                <TableCell>
                  <Chip label={STATUS_LABELS[r.status] || r.status}
                    color={STATUS_COLORS[r.status] || 'default'} size="small" />
                </TableCell>
                <TableCell>{new Date(r.created_at).toLocaleDateString()}</TableCell>
                <TableCell>
                  <Tooltip title="Ver detalle">
                    <IconButton size="small" onClick={() => viewDetail(r.id)}><Visibility /></IconButton>
                  </Tooltip>
                  {canApproveManager && r.status === 'PENDIENTE_GERENTE' && (
                    <Tooltip title="Aprobar">
                      <IconButton size="small" color="success"
                        onClick={() => handleAction(r.id, 'approve_manager')}><Check /></IconButton>
                    </Tooltip>
                  )}
                  {canApproveFinal && r.status === 'APROBADA_POR_GERENTE' && (
                    <Tooltip title="Aprobar Final">
                      <IconButton size="small" color="success"
                        onClick={() => handleAction(r.id, 'approve_final')}><Check /></IconButton>
                    </Tooltip>
                  )}
                  {(canApproveManager || canApproveFinal) &&
                    ['PENDIENTE_GERENTE', 'APROBADA_POR_GERENTE'].includes(r.status) && (
                    <Tooltip title="Rechazar">
                      <IconButton size="small" color="error"
                        onClick={() => {
                          const reason = prompt('Motivo del rechazo:');
                          if (reason) handleAction(r.id, 'reject', { reason });
                        }}><Close /></IconButton>
                    </Tooltip>
                  )}
                  {r.status === 'PENDIENTE_GERENTE' && r.requester === user?.id && (
                    <Tooltip title="Cancelar">
                      <IconButton size="small" onClick={() => handleAction(r.id, 'cancel')}>
                        <Cancel />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination component="div" count={count} page={page} onPageChange={(_, p) => setPage(p)}
          rowsPerPage={20} rowsPerPageOptions={[20]} />
      </TableContainer>

      {/* Dialog: Nueva Solicitud */}
      <Dialog open={openNew} onClose={() => setOpenNew(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nueva Solicitud de Compra</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField select fullWidth label="Categoria" margin="normal" value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value, items: [] })}>
            {categories.map(c => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
          </TextField>
          <TextField select fullWidth label="Items" margin="normal" value={form.items}
            onChange={(e) => setForm({ ...form, items: e.target.value })}
            SelectProps={{ multiple: true }}>
            {filteredItems.map(i => <MenuItem key={i.id} value={i.id}>{i.name}</MenuItem>)}
          </TextField>
          <TextField fullWidth label="Descripcion" margin="normal" multiline rows={2}
            value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <TextField fullWidth label="Monto Estimado" margin="normal" type="number"
            value={form.estimated_amount} onChange={(e) => setForm({ ...form, estimated_amount: e.target.value })} />
          <TextField fullWidth label="Fecha Requerida" margin="normal" type="date"
            value={form.required_date} onChange={(e) => setForm({ ...form, required_date: e.target.value })}
            InputLabelProps={{ shrink: true }} />
          <TextField fullWidth label="Justificacion" margin="normal" multiline rows={2}
            value={form.justification} onChange={(e) => setForm({ ...form, justification: e.target.value })} />
          <TextField select fullWidth label="Urgencia" margin="normal" value={form.urgency}
            onChange={(e) => setForm({ ...form, urgency: e.target.value })}>
            <MenuItem value="NORMAL">Normal</MenuItem>
            <MenuItem value="URGENTE">Urgente</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenNew(false)}>Cancelar</Button>
          <Button variant="contained" onClick={handleCreate}>Crear Solicitud</Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Detalle */}
      <Dialog open={openDetail} onClose={() => { setOpenDetail(false); setUploadError(''); }} maxWidth="md" fullWidth>
        <DialogTitle>Solicitud {selected?.request_number}</DialogTitle>
        <DialogContent>
          {selected && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Estado: <Chip label={STATUS_LABELS[selected.status]} color={STATUS_COLORS[selected.status]} size="small" />
              </Typography>
              <Typography sx={{ mt: 1 }}><strong>Solicitante:</strong> {selected.requester_name}</Typography>
              <Typography><strong>Centro de Costos:</strong> {selected.cost_center_name}</Typography>
              <Typography><strong>Categoria:</strong> {selected.category_name}</Typography>
              <Typography><strong>Monto Estimado:</strong> ${Number(selected.estimated_amount).toLocaleString()}</Typography>
              <Typography><strong>Fecha Requerida:</strong> {selected.required_date}</Typography>
              <Typography><strong>Urgencia:</strong> {selected.urgency_display}</Typography>
              <Typography sx={{ mt: 1 }}><strong>Descripcion:</strong> {selected.description}</Typography>
              <Typography><strong>Justificacion:</strong> {selected.justification}</Typography>
              {selected.exceeds_budget && (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  Esta solicitud excede el presupuesto disponible.
                  {selected.budget_excess_justification && (
                    <Typography variant="body2">Justificacion: {selected.budget_excess_justification}</Typography>
                  )}
                </Alert>
              )}
              {selected.rejection_reason && (
                <Alert severity="error" sx={{ mt: 1 }}>
                  <strong>Motivo de rechazo:</strong> {selected.rejection_reason}
                </Alert>
              )}
              {selected.actual_supplier && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2">Datos de Compra</Typography>
                  <Typography variant="body2">Proveedor: {selected.actual_supplier}</Typography>
                  <Typography variant="body2">Monto Real: ${Number(selected.actual_amount).toLocaleString()}</Typography>
                  <Typography variant="body2">Factura: {selected.invoice_number}</Typography>
                </Box>
              )}

              {/* Archivos Adjuntos */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <AttachFile fontSize="small" />
                  Archivos Adjuntos ({selected.attachments?.length || 0}/10)
                </Typography>
                {selected.attachments?.length > 0 ? (
                  <List dense>
                    {selected.attachments.map(att => (
                      <ListItem key={att.id} sx={{ bgcolor: 'grey.50', borderRadius: 1, mb: 0.5 }}>
                        <ListItemIcon><PictureAsPdf color="error" /></ListItemIcon>
                        <ListItemText
                          primary={att.original_filename}
                          secondary={`${att.file_size_display} - Subido por ${att.uploaded_by_name}`}
                        />
                        <ListItemSecondaryAction>
                          <Tooltip title="Descargar">
                            <IconButton size="small" component="a" href={att.file} target="_blank" rel="noopener">
                              <CloudUpload fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          {(att.uploaded_by === user?.id || canApproveFinal) && (
                            <Tooltip title="Eliminar">
                              <IconButton size="small" color="error"
                                onClick={() => handleDeleteAttachment(att.id)}>
                                <Delete fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">No hay archivos adjuntos</Typography>
                )}

                {/* Upload button - visible if less than 10 attachments */}
                {(selected.attachments?.length || 0) < 10 && (
                  <Box sx={{ mt: 1 }}>
                    {uploadError && <Alert severity="error" sx={{ mb: 1 }}>{uploadError}</Alert>}
                    {uploading && <LinearProgress sx={{ mb: 1 }} />}
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf"
                      style={{ display: 'none' }}
                      onChange={handleFileUpload}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<AttachFile />}
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                    >
                      Adjuntar PDF
                    </Button>
                  </Box>
                )}
              </Box>

              {/* Comentarios */}
              {selected.comments?.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Comentarios</Typography>
                  {selected.comments.map(c => (
                    <Box key={c.id} sx={{ p: 1, mb: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">{c.user_name}</Typography>
                      <Typography variant="body2">{c.comment}</Typography>
                    </Box>
                  ))}
                </Box>
              )}

              {/* Historial de estados */}
              {selected.status_history?.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Historial de Estados</Typography>
                  {selected.status_history.map(h => (
                    <Box key={h.id} sx={{ p: 1, mb: 0.5, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {h.changed_by_name} - {new Date(h.created_at).toLocaleString()}
                      </Typography>
                      <Typography variant="body2">
                        {h.previous_status_display} &rarr; {h.new_status_display}
                        {h.notes && ` - ${h.notes}`}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setOpenDetail(false); setUploadError(''); }}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
