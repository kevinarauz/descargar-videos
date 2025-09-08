#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Response Helper - Helper para respuestas HTTP/JSON
=================================================

Clase utilitaria para estandarizar respuestas HTTP/JSON y
manejo de errores en endpoints de Flask.

Autor: M3U8 Downloader System
Propósito: Centralizar el manejo de respuestas para reducir código duplicado
"""

import json
from typing import Dict, Any, Optional, Union, List
from flask import jsonify

class ResponseHelper:
    """Helper para generar respuestas HTTP/JSON estandarizadas"""
    
    @staticmethod
    def success(data: Optional[Dict[str, Any]] = None, 
                message: str = "Operación exitosa") -> Dict[str, Any]:
        """
        Genera respuesta de éxito estandarizada
        
        Args:
            data: Datos a incluir en la respuesta
            message: Mensaje descriptivo
            
        Returns:
            Dict con respuesta de éxito
        """
        response = {
            'success': True,
            'message': message
        }
        
        if data:
            response.update(data)
            
        return response
    
    @staticmethod
    def error(message: str, 
              code: Optional[str] = None, 
              details: Optional[Dict[str, Any]] = None,
              status_code: int = 400) -> Dict[str, Any]:
        """
        Genera respuesta de error estandarizada
        
        Args:
            message: Mensaje de error
            code: Código de error opcional
            details: Detalles adicionales del error
            status_code: Código HTTP de estado
            
        Returns:
            Dict con respuesta de error
        """
        response = {
            'success': False,
            'error': message,
            'status_code': status_code
        }
        
        if code:
            response['error_code'] = code
            
        if details:
            response['details'] = details
            
        return response
    
    @staticmethod
    def progress_response(progress_id: str, 
                         current: int, 
                         total: int, 
                         status: str = "processing",
                         additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Genera respuesta de progreso estandarizada
        
        Args:
            progress_id: ID del progreso
            current: Elemento actual procesado
            total: Total de elementos
            status: Estado del progreso
            additional_data: Datos adicionales
            
        Returns:
            Dict con respuesta de progreso
        """
        porcentaje = (current / total * 100) if total > 0 else 0
        
        response = {
            'success': True,
            'progress_id': progress_id,
            'status': status,
            'current': current,
            'total': total,
            'porcentaje': round(porcentaje, 2)
        }
        
        if additional_data:
            response.update(additional_data)
            
        return response
    
    @staticmethod
    def list_response(items: List[Any], 
                      total_count: Optional[int] = None,
                      page: int = 1,
                      per_page: Optional[int] = None) -> Dict[str, Any]:
        """
        Genera respuesta de lista paginada
        
        Args:
            items: Lista de elementos
            total_count: Total de elementos (si es diferente a len(items))
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict con respuesta de lista
        """
        response = {
            'success': True,
            'items': items,
            'count': len(items),
            'page': page
        }
        
        if total_count is not None:
            response['total_count'] = total_count
            
        if per_page is not None:
            response['per_page'] = per_page
            response['total_pages'] = (total_count or len(items)) // per_page + 1
            
        return response
    
    @staticmethod
    def clean_bytes_objects(obj: Any) -> Any:
        """
        Limpia objetos bytes para serialización JSON recursivamente
        
        Args:
            obj: Objeto a limpiar
            
        Returns:
            Objeto limpio sin bytes objects
        """
        if isinstance(obj, bytes):
            return f"<bytes object: {len(obj)} bytes>"
        elif isinstance(obj, dict):
            return {k: ResponseHelper.clean_bytes_objects(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ResponseHelper.clean_bytes_objects(item) for item in obj]
        else:
            return obj
    
    @staticmethod
    def safe_jsonify(data: Any, **kwargs) -> Any:
        """
        Wrapper seguro para jsonify que limpia bytes objects
        
        Args:
            data: Datos a serializar
            **kwargs: Argumentos adicionales para jsonify
            
        Returns:
            Respuesta JSON Flask
        """
        clean_data = ResponseHelper.clean_bytes_objects(data)
        return jsonify(clean_data, **kwargs)
    
    @staticmethod
    def drm_analysis_response(drm_detected: bool,
                             encryption_methods: List[str],
                             aes_keys: List[Dict[str, Any]],
                             total_segments: int,
                             analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Respuesta específica para análisis DRM
        
        Args:
            drm_detected: Si se detectó DRM
            encryption_methods: Métodos de encriptación encontrados
            aes_keys: Claves AES encontradas
            total_segments: Total de segmentos
            analysis_data: Datos de análisis completos
            
        Returns:
            Dict con respuesta de análisis DRM
        """
        has_aes128 = 'AES-128' in encryption_methods
        
        return ResponseHelper.success({
            'drm_detected': drm_detected,
            'encryption_methods': encryption_methods,
            'has_aes128': has_aes128,
            'aes_keys': ResponseHelper.clean_bytes_objects(aes_keys),
            'total_segments': total_segments,
            'analysis_data': ResponseHelper.clean_bytes_objects(analysis_data)
        }, "Análisis DRM completado")
    
    @staticmethod
    def download_started_response(download_id: str,
                                 url: str,
                                 output_file: str,
                                 operation_type: str = "download") -> Dict[str, Any]:
        """
        Respuesta para descarga iniciada
        
        Args:
            download_id: ID de la descarga
            url: URL siendo descargada
            output_file: Archivo de salida
            operation_type: Tipo de operación
            
        Returns:
            Dict con respuesta de descarga iniciada
        """
        return ResponseHelper.success({
            'download_id': download_id,
            'url': url,
            'output_file': output_file,
            'operation_type': operation_type
        }, f"{operation_type.title()} iniciado correctamente")
    
    @staticmethod
    def validation_error(field: str, message: str) -> Dict[str, Any]:
        """
        Error de validación específico
        
        Args:
            field: Campo que falló la validación
            message: Mensaje de error
            
        Returns:
            Dict con error de validación
        """
        return ResponseHelper.error(
            message=f"Error de validación en {field}: {message}",
            code="VALIDATION_ERROR",
            details={'field': field, 'validation_message': message}
        )


# Instancia global del helper
response_helper = ResponseHelper()