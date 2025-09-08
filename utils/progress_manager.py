#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progress Manager - Gestor de Progreso para M3U8 Downloader
=========================================================

Clase utilitaria para manejar el progreso de descargas y operaciones.
Mantiene el estado, calcula tiempos y proporciona callbacks.

Autor: M3U8 Downloader System
Propósito: Centralizar la gestión de progreso para reducir complejidad en app.py
"""

import time
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime

class ProgressManager:
    """Gestor centralizado de progreso para descargas y operaciones"""
    
    def __init__(self):
        self.progress_data = {}
        self.callbacks = {}
    
    def create_progress(self, 
                       progress_id: str, 
                       url: str, 
                       output_file: str, 
                       total_items: int = 0,
                       operation_type: str = "download") -> Dict[str, Any]:
        """
        Crea un nuevo registro de progreso
        
        Args:
            progress_id: ID único del progreso
            url: URL siendo procesada
            output_file: Archivo de salida
            total_items: Total de elementos a procesar
            operation_type: Tipo de operación (download, decrypt, merge)
            
        Returns:
            Dict con datos iniciales de progreso
        """
        progress = {
            'id': progress_id,
            'url': url,
            'status': 'initializing',
            'porcentaje': 0,
            'current': 0,
            'total': total_items,
            'start_time': time.time(),
            'output_file': output_file,
            'operation_type': operation_type,
            'quality': 'Processing',
            'elapsed_time': 0,
            'estimated_time_remaining': None,
            'download_speed_mbps': 0,
            'segments_per_minute': 0,
            'created_at': datetime.now().isoformat()
        }
        
        self.progress_data[progress_id] = progress
        return progress
    
    def update_progress(self, 
                       progress_id: str, 
                       current: Optional[int] = None,
                       total: Optional[int] = None,
                       status: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        Actualiza un registro de progreso
        
        Args:
            progress_id: ID del progreso
            current: Elemento actual procesado
            total: Total de elementos
            status: Estado actual
            **kwargs: Campos adicionales a actualizar
            
        Returns:
            Dict con datos actualizados de progreso
        """
        if progress_id not in self.progress_data:
            raise ValueError(f"Progress ID {progress_id} no existe")
        
        progress = self.progress_data[progress_id]
        
        # Actualizar campos proporcionados
        if current is not None:
            progress['current'] = current
        if total is not None:
            progress['total'] = total
        if status is not None:
            progress['status'] = status
            
        # Actualizar campos adicionales
        progress.update(kwargs)
        
        # Calcular métricas automáticamente
        if progress['total'] > 0:
            progress['porcentaje'] = (progress['current'] / progress['total']) * 100
        
        progress['elapsed_time'] = time.time() - progress['start_time']
        
        # Calcular tiempo restante estimado
        if progress['current'] > 0 and progress['total'] > 0:
            rate = progress['current'] / progress['elapsed_time']
            remaining_items = progress['total'] - progress['current']
            if rate > 0:
                progress['estimated_time_remaining'] = remaining_items / rate
                progress['segments_per_minute'] = rate * 60
        
        progress['last_updated'] = datetime.now().isoformat()
        
        # Ejecutar callback si existe
        if progress_id in self.callbacks:
            try:
                self.callbacks[progress_id](progress)
            except Exception as e:
                print(f"Error ejecutando callback para {progress_id}: {e}")
        
        return progress
    
    def set_callback(self, progress_id: str, callback: Callable[[Dict[str, Any]], None]):
        """Establece un callback para actualizaciones de progreso"""
        self.callbacks[progress_id] = callback
    
    def get_progress(self, progress_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de progreso por ID"""
        return self.progress_data.get(progress_id)
    
    def complete_progress(self, progress_id: str, success: bool = True, **kwargs) -> Dict[str, Any]:
        """Marca un progreso como completado"""
        status = 'completed' if success else 'failed'
        return self.update_progress(progress_id, status=status, porcentaje=100, **kwargs)
    
    def remove_progress(self, progress_id: str):
        """Elimina un registro de progreso"""
        self.progress_data.pop(progress_id, None)
        self.callbacks.pop(progress_id, None)
    
    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todos los registros de progreso"""
        return self.progress_data.copy()
    
    def get_active_progress(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene solo los progresos activos (no completados ni fallidos)"""
        return {
            pid: data for pid, data in self.progress_data.items()
            if data['status'] not in ['completed', 'failed', 'cancelled']
        }
    
    def format_time(self, seconds: float) -> str:
        """Formatea tiempo en segundos a formato legible"""
        if seconds is None or seconds < 0:
            return "N/A"
        
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        
        if minutes > 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}h {minutes}m {secs}s"
        else:
            return f"{minutes}m {secs}s"
    
    def get_progress_summary(self, progress_id: str) -> str:
        """Genera un resumen textual del progreso"""
        progress = self.get_progress(progress_id)
        if not progress:
            return f"Progress {progress_id} no encontrado"
        
        elapsed = self.format_time(progress['elapsed_time'])
        remaining = self.format_time(progress.get('estimated_time_remaining'))
        
        return (f"🔄 {progress['operation_type'].title()}: "
                f"{progress['current']}/{progress['total']} "
                f"({progress['porcentaje']:.1f}%) | "
                f"⏱️ {elapsed} | "
                f"⏳ {remaining}")
    
    def export_progress(self, progress_id: str) -> str:
        """Exporta progreso a JSON"""
        progress = self.get_progress(progress_id)
        if not progress:
            return "{}"
        return json.dumps(progress, indent=2)
    
    def cleanup_completed(self, max_age_hours: int = 24):
        """Limpia progresos completados más antiguos que max_age_hours"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        to_remove = []
        for pid, data in self.progress_data.items():
            if (data['status'] in ['completed', 'failed'] and 
                data['start_time'] < cutoff_time):
                to_remove.append(pid)
        
        for pid in to_remove:
            self.remove_progress(pid)
        
        return len(to_remove)


# Instancia global del gestor de progreso
progress_manager = ProgressManager()


def create_progress_callback(progress_id: str):
    """Factory para crear callbacks de progreso estándar"""
    def callback(data):
        # Callback que actualiza automáticamente el gestor de progreso
        progress_manager.update_progress(
            progress_id,
            current=data.get('current', 0),
            total=data.get('total', 0),
            status=data.get('status', 'processing'),
            **{k: v for k, v in data.items() if k not in ['current', 'total', 'status']}
        )
    return callback