import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from app.workers.sqs_worker import (
    _parse_message_data,
    _formatear_error_csv,
    _aplicar_resultado_job,
    _procesar_mensaje_local,
    procesar_mensaje,
    CSVImportError
)
from app.models.import_job import ImportJob

class TestWorkerCoverage:
    """Tests para mejorar la cobertura de sqs_worker.py"""

    def test_parse_message_data(self):
        """Test: _parse_message_data con diferentes tipos de entrada"""
        # Bytes
        assert _parse_message_data(b'{"key": "value"}') == {"key": "value"}
        # String
        assert _parse_message_data('{"key": "value"}') == {"key": "value"}
        # Dict
        assert _parse_message_data({"key": "value"}) == {"key": "value"}
        # Invalid JSON
        assert _parse_message_data('invalid json') is None
        # Invalid type
        assert _parse_message_data(123) is None

    def test_formatear_error_csv(self):
        """Test: _formatear_error_csv"""
        # Dict
        error_dict = {"codigo": "ERROR", "mensaje": "Detalle"}
        assert json.loads(_formatear_error_csv(error_dict)) == error_dict
        # String
        assert _formatear_error_csv("Error simple") == "Error simple"

    def test_aplicar_resultado_job(self, app):
        """Test: _aplicar_resultado_job actualiza el job correctamente"""
        with app.app_context():
            job = Mock(spec=ImportJob)
            resultado = {
                'exitosos': 10,
                'fallidos': 150,
                'detalles_errores': [{'error': i} for i in range(150)]
            }
            
            _aplicar_resultado_job(job, resultado)
            
            # Verificar actualización de progreso
            job.actualizar_progreso.assert_called_with(
                filas_procesadas=160,
                exitosos=10,
                fallidos=150
            )
            
            # Verificar truncado de errores
            assert job.detalles_errores['total_errores'] == 150
            assert job.detalles_errores['errores_capturados'] == 100
            assert len(job.detalles_errores['errores']) == 100
            assert job.detalles_errores['nota'] == 'Mostrando primeros 100 errores'
            
            # Verificar marcado como completado
            job.marcar_como_completado.assert_called()

    @patch('app.workers.sqs_worker.db')
    def test_procesar_mensaje_local_sin_job_id(self, mock_db, app):
        """Test: _procesar_mensaje_local falla si no hay job_id"""
        payload = {'local_path': '/tmp/file.csv'}
        assert _procesar_mensaje_local(app, payload) is False

    @patch('app.workers.sqs_worker.db')
    def test_procesar_mensaje_local_job_no_encontrado(self, mock_db, app):
        """Test: _procesar_mensaje_local falla si job no existe en DB"""
        payload = {'job_id': '999', 'local_path': '/tmp/file.csv'}
        
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = None
        
        assert _procesar_mensaje_local(app, payload) is False

    @patch('app.workers.sqs_worker.db')
    @patch('os.path.exists')
    def test_procesar_mensaje_local_archivo_no_existe(self, mock_exists, mock_db, app):
        """Test: _procesar_mensaje_local falla si archivo no existe"""
        payload = {'job_id': '1', 'local_path': '/tmp/missing.csv'}
        
        job = Mock(spec=ImportJob)
        job.local_path = None
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = job
        mock_exists.return_value = False
        
        assert _procesar_mensaje_local(app, payload) is False
        job.marcar_como_fallido.assert_called_with("Archivo CSV no encontrado en disco: /tmp/missing.csv")

    @patch('app.workers.sqs_worker.db')
    @patch('os.path.exists')
    @patch('app.workers.sqs_worker.LocalImportService')
    def test_procesar_mensaje_local_error_lectura(self, mock_local_service, mock_exists, mock_db, app):
        """Test: _procesar_mensaje_local falla si hay error leyendo CSV"""
        payload = {'job_id': '1', 'local_path': '/tmp/file.csv'}
        
        job = Mock(spec=ImportJob)
        job.local_path = '/tmp/file.csv'
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = job
        mock_exists.return_value = True
        mock_local_service.leer_csv.side_effect = Exception("Read error")
        
        assert _procesar_mensaje_local(app, payload) is False
        job.marcar_como_fallido.assert_called()
        assert "Read error" in job.marcar_como_fallido.call_args[0][0]

    @patch('app.workers.sqs_worker.db')
    @patch('os.path.exists')
    @patch('app.workers.sqs_worker.LocalImportService')
    @patch('app.workers.sqs_worker.CSVProductoService')
    def test_procesar_mensaje_local_exito(self, mock_csv_service, mock_local_service, mock_exists, mock_db, app):
        """Test: _procesar_mensaje_local flujo exitoso"""
        payload = {'job_id': '1', 'local_path': '/tmp/file.csv', 'usuario_registro': 'user1'}
        
        job = Mock(spec=ImportJob)
        job.local_path = '/tmp/file.csv'
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = job
        mock_exists.return_value = True
        mock_local_service.leer_csv.return_value = "header\nrow1"
        
        mock_csv_instance = mock_csv_service.return_value
        mock_csv_instance.procesar_csv_desde_contenido.return_value = {'exitosos': 1, 'fallidos': 0}
        
        assert _procesar_mensaje_local(app, payload) is True
        
        # Verificar llamadas
        job.marcar_como_procesando.assert_called()
        mock_csv_instance.procesar_csv_desde_contenido.assert_called()
        job.marcar_como_completado.assert_called()

    @patch('app.workers.sqs_worker.db')
    @patch('os.path.exists')
    @patch('app.workers.sqs_worker.LocalImportService')
    @patch('app.workers.sqs_worker.CSVProductoService')
    def test_procesar_mensaje_local_csv_error(self, mock_csv_service, mock_local_service, mock_exists, mock_db, app):
        """Test: _procesar_mensaje_local captura CSVImportError"""
        payload = {'job_id': '1', 'local_path': '/tmp/file.csv'}
        
        job = Mock(spec=ImportJob)
        job.local_path = '/tmp/file.csv'
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = job
        mock_exists.return_value = True
        
        mock_csv_instance = mock_csv_service.return_value
        mock_csv_instance.procesar_csv_desde_contenido.side_effect = CSVImportError({'codigo': 'ERROR'})
        
        assert _procesar_mensaje_local(app, payload) is False
        job.marcar_como_fallido.assert_called()

    def test_procesar_mensaje_wrapper(self, app):
        """Test: procesar_mensaje wrapper logic"""
        # Caso SQS (dict con Body)
        with patch('app.workers.sqs_worker._procesar_mensaje_sqs') as mock_sqs:
            procesar_mensaje(app, {'Body': '{}'})
            mock_sqs.assert_called()
            
        # Caso Local (dict sin Body)
        with patch('app.workers.sqs_worker._procesar_mensaje_local') as mock_local:
            procesar_mensaje(app, {'job_id': '1'})
            mock_local.assert_called()
            
        # Caso String JSON válido
        with patch('app.workers.sqs_worker._procesar_mensaje_local') as mock_local:
            procesar_mensaje(app, '{"job_id": "1"}')
            mock_local.assert_called()
            
        # Caso String inválido
        assert procesar_mensaje(app, 'invalid') is False
        
        # Caso Tipo inválido
        assert procesar_mensaje(app, 123) is False
