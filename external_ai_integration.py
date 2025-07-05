"""
External AI Integration for Direct Code Manipulation
Allows external AI services to read, write, and modify project files directly
"""

import os
import json
import requests
from typing import Dict, List, Any
from pathlib import Path

class ExternalAICodeEditor:
    """Interface for external AI to directly edit project code"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.editable_extensions = {'.py', '.js', '.html', '.css', '.json', '.md', '.txt'}
        self.protected_files = {'requirements.txt', 'pyproject.toml', '.env'}
        
    def get_project_structure(self) -> Dict[str, Any]:
        """Get complete project structure for AI context"""
        structure = {}
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and not self._is_protected_path(file_path):
                relative_path = str(file_path.relative_to(self.project_root))
                structure[relative_path] = {
                    'type': 'file',
                    'extension': file_path.suffix,
                    'size': file_path.stat().st_size,
                    'editable': file_path.suffix in self.editable_extensions
                }
        
        return structure
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file content for AI analysis"""
        try:
            full_path = self.project_root / file_path
            
            if not self._is_safe_to_read(full_path):
                return {'error': 'File not accessible or protected'}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'success': True,
                'content': content,
                'lines': len(content.splitlines()),
                'size': len(content)
            }
            
        except Exception as e:
            return {'error': f'Failed to read file: {str(e)}'}
    
    def write_file(self, file_path: str, content: str, backup: bool = True) -> Dict[str, Any]:
        """Write/modify file content with backup option"""
        try:
            full_path = self.project_root / file_path
            
            if not self._is_safe_to_write(full_path):
                return {'error': 'File not writable or protected'}
            
            # Create backup if requested
            if backup and full_path.exists():
                backup_path = full_path.with_suffix(full_path.suffix + '.backup')
                with open(full_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # Write new content
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'message': f'File {file_path} updated successfully',
                'backup_created': backup and full_path.with_suffix(full_path.suffix + '.backup').exists()
            }
            
        except Exception as e:
            return {'error': f'Failed to write file: {str(e)}'}
    
    def create_new_file(self, file_path: str, content: str = '') -> Dict[str, Any]:
        """Create a new file with optional content"""
        try:
            full_path = self.project_root / file_path
            
            if full_path.exists():
                return {'error': 'File already exists'}
            
            if not self._is_safe_to_write(full_path):
                return {'error': 'File path not allowed'}
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'message': f'File {file_path} created successfully'
            }
            
        except Exception as e:
            return {'error': f'Failed to create file: {str(e)}'}
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a file (with safety checks)"""
        try:
            full_path = self.project_root / file_path
            
            if not self._is_safe_to_delete(full_path):
                return {'error': 'File not safe to delete or protected'}
            
            if not full_path.exists():
                return {'error': 'File does not exist'}
            
            full_path.unlink()
            
            return {
                'success': True,
                'message': f'File {file_path} deleted successfully'
            }
            
        except Exception as e:
            return {'error': f'Failed to delete file: {str(e)}'}
    
    def search_in_files(self, search_term: str, file_extensions: List[str] = None) -> Dict[str, Any]:
        """Search for text across project files"""
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.html', '.css']
        
        results = []
        
        for file_path in self.project_root.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in file_extensions and 
                not self._is_protected_path(file_path)):
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if search_term.lower() in line.lower():
                            results.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'content': line.strip()
                            })
                            
                except Exception:
                    continue  # Skip files that can't be read
        
        return {
            'success': True,
            'results': results,
            'total_matches': len(results)
        }
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Get available API endpoints for external AI access"""
        return {
            'read_file': '/ai-api/read-file',
            'write_file': '/ai-api/write-file',
            'create_file': '/ai-api/create-file',
            'delete_file': '/ai-api/delete-file',
            'project_structure': '/ai-api/project-structure',
            'search_files': '/ai-api/search-files',
            'execute_code': '/ai-api/execute-code'
        }
    
    def _is_protected_path(self, path: Path) -> bool:
        """Check if path is in protected directories or files"""
        protected_dirs = {'__pycache__', '.git', 'node_modules', 'venv', '.env'}
        protected_files = self.protected_files
        
        # Check if any part of the path is protected
        for part in path.parts:
            if part in protected_dirs:
                return True
        
        # Check if filename is protected
        if path.name in protected_files:
            return True
        
        return False
    
    def _is_safe_to_read(self, path: Path) -> bool:
        """Check if file is safe to read"""
        if not path.exists() or not path.is_file():
            return False
        
        if self._is_protected_path(path):
            return False
        
        # Check file size (limit to 10MB)
        if path.stat().st_size > 10 * 1024 * 1024:
            return False
        
        return True
    
    def _is_safe_to_write(self, path: Path) -> bool:
        """Check if file is safe to write"""
        if self._is_protected_path(path):
            return False
        
        # Only allow certain extensions
        if path.suffix not in self.editable_extensions:
            return False
        
        return True
    
    def _is_safe_to_delete(self, path: Path) -> bool:
        """Check if file is safe to delete"""
        if self._is_protected_path(path):
            return False
        
        # Don't allow deletion of core application files
        core_files = {'main.py', 'app.py', 'routes.py', 'models.py'}
        if path.name in core_files:
            return False
        
        return True

# Global instance for external AI access
external_ai_editor = ExternalAICodeEditor()

def setup_ai_api_routes(app):
    """Setup API routes for external AI access"""
    
    @app.route('/ai-api/project-structure', methods=['GET'])
    def get_project_structure():
        """Get project structure for AI context"""
        from flask import jsonify
        structure = external_ai_editor.get_project_structure()
        return jsonify(structure)
    
    @app.route('/ai-api/read-file', methods=['POST'])
    def read_file():
        """Read file content"""
        from flask import request, jsonify
        data = request.get_json()
        
        if not data or 'file_path' not in data:
            return jsonify({'error': 'file_path required'}), 400
        
        result = external_ai_editor.read_file(data['file_path'])
        return jsonify(result)
    
    @app.route('/ai-api/write-file', methods=['POST'])
    def write_file():
        """Write/modify file content"""
        from flask import request, jsonify
        data = request.get_json()
        
        if not data or 'file_path' not in data or 'content' not in data:
            return jsonify({'error': 'file_path and content required'}), 400
        
        backup = data.get('backup', True)
        result = external_ai_editor.write_file(data['file_path'], data['content'], backup)
        return jsonify(result)
    
    @app.route('/ai-api/create-file', methods=['POST'])
    def create_file():
        """Create new file"""
        from flask import request, jsonify
        data = request.get_json()
        
        if not data or 'file_path' not in data:
            return jsonify({'error': 'file_path required'}), 400
        
        content = data.get('content', '')
        result = external_ai_editor.create_new_file(data['file_path'], content)
        return jsonify(result)
    
    @app.route('/ai-api/search-files', methods=['POST'])
    def search_files():
        """Search across project files"""
        from flask import request, jsonify
        data = request.get_json()
        
        if not data or 'search_term' not in data:
            return jsonify({'error': 'search_term required'}), 400
        
        extensions = data.get('extensions', ['.py', '.js', '.html', '.css'])
        result = external_ai_editor.search_in_files(data['search_term'], extensions)
        return jsonify(result)
    
    return app