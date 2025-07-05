#!/usr/bin/env python3
"""
External AI Code Manipulation Demo
Demonstrates how external AI can interact with the Visitor Intel platform code
"""

import requests
import json
import time

class ExternalAIDemo:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.ai_api_base = f"{base_url}/ai-api"
        
    def demo_project_analysis(self):
        """Demonstrate external AI analyzing the project"""
        print("🤖 External AI: Analyzing Visitor Intel project...")
        
        # 1. Get project structure
        structure = self.get_project_structure()
        if structure:
            print(f"   📁 Found {len(structure)} files in project")
            python_files = [f for f, info in structure.items() if f.endswith('.py')]
            print(f"   🐍 Python files: {len(python_files)}")
            
        # 2. Analyze main application file
        main_content = self.read_file('main.py')
        if main_content:
            print(f"   📄 main.py: {main_content['lines']} lines")
            
        # 3. Search for AI-related code
        ai_references = self.search_files('ai', ['.py'])
        if ai_references:
            print(f"   🔍 Found {ai_references['total_matches']} AI-related code references")
            
        return True
    
    def demo_code_enhancement(self):
        """Demonstrate external AI enhancing existing code"""
        print("🤖 External AI: Enhancing code with new features...")
        
        # Create a new AI-powered feature
        new_feature_code = '''"""
AI-Powered Code Quality Analyzer
Added by External AI to demonstrate code enhancement capabilities
"""

import ast
import os
from typing import Dict, List, Any

class CodeQualityAnalyzer:
    """Analyzes Python code quality and suggests improvements"""
    
    def __init__(self):
        self.issues = []
        
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a Python file for quality issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            analysis = {
                'file': file_path,
                'lines': len(content.splitlines()),
                'functions': self._count_functions(tree),
                'classes': self._count_classes(tree),
                'complexity_score': self._calculate_complexity(tree),
                'suggestions': self._generate_suggestions(tree, content)
            }
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _count_functions(self, tree) -> int:
        """Count function definitions"""
        return len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
    
    def _count_classes(self, tree) -> int:
        """Count class definitions"""
        return len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
    
    def _calculate_complexity(self, tree) -> int:
        """Calculate basic complexity score"""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
        return complexity
    
    def _generate_suggestions(self, tree, content: str) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Check for long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    func_length = node.end_lineno - node.lineno
                    if func_length > 50:
                        suggestions.append(f"Function '{node.name}' is {func_length} lines long. Consider breaking it down.")
        
        # Check for missing docstrings
        lines = content.splitlines()
        has_docstring = any('"""' in line for line in lines[:10])
        if len(lines) > 5 and not has_docstring:
            suggestions.append("Consider adding module docstring")
        
        return suggestions

# Usage example for the Visitor Intel platform
def analyze_visitor_intel_codebase():
    """Analyze the Visitor Intel codebase quality"""
    analyzer = CodeQualityAnalyzer()
    
    # Analyze key files
    key_files = ['main.py', 'routes.py', 'ai_conversation.py', 'models.py']
    
    for file_path in key_files:
        if os.path.exists(file_path):
            analysis = analyzer.analyze_file(file_path)
            print(f"Analysis for {file_path}:", analysis)
    
    return "Code quality analysis complete"

if __name__ == "__main__":
    analyze_visitor_intel_codebase()
'''
        
        # Create the new file
        result = self.create_file('ai_code_analyzer.py', new_feature_code)
        if result and result.get('success'):
            print("   ✅ Created ai_code_analyzer.py with AI-powered code quality analysis")
            
        # Enhance existing file with improvement
        routes_content = self.read_file('routes.py')
        if routes_content and routes_content.get('success'):
            content = routes_content['content']
            
            # Add new route for code analysis
            enhancement = '''
@app.route('/ai-analysis')
def ai_code_analysis():
    """AI-powered code quality analysis endpoint - Added by External AI"""
    try:
        from ai_code_analyzer import analyze_visitor_intel_codebase
        result = analyze_visitor_intel_codebase()
        return jsonify({
            'success': True,
            'message': 'Code analysis complete',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''
            
            # Add before the error handlers
            enhanced_content = content.replace(
                '# Setup External AI API Routes',
                enhancement + '\n# Setup External AI API Routes'
            )
            
            write_result = self.write_file('routes.py', enhanced_content)
            if write_result and write_result.get('success'):
                print("   ✅ Enhanced routes.py with AI code analysis endpoint")
                
        return True
    
    def demo_documentation_generation(self):
        """Demonstrate external AI generating documentation"""
        print("🤖 External AI: Generating project documentation...")
        
        # Generate comprehensive documentation
        documentation = '''# Visitor Intel Platform - External AI Integration

## Overview
The Visitor Intel platform now supports external AI collaboration through a comprehensive API interface.

## External AI Integration Features

### 1. Code Access API
- **Read Files**: `POST /ai-api/read-file`
- **Write Files**: `POST /ai-api/write-file`
- **Create Files**: `POST /ai-api/create-file`
- **Project Structure**: `GET /ai-api/project-structure`
- **Search Files**: `POST /ai-api/search-files`

### 2. Web Interface
Access the external AI interface at: `/external-ai`

### 3. Safety Features
- Protected file filtering (prevents access to sensitive files)
- Automatic backups when modifying files
- File size limits and extension restrictions
- Read-only access to system files

### 4. AI Capabilities
- Project structure analysis
- Code quality assessment
- Automated documentation generation
- Feature enhancement suggestions
- Bug detection and fixing

## Usage Examples

### Reading Project Files
```python
import requests

response = requests.post('http://localhost:5000/ai-api/read-file', 
    json={'file_path': 'main.py'})
result = response.json()
print(result['content'])
```

### Creating New Features
```python
new_code = """
def new_ai_feature():
    return "Generated by External AI"
"""

response = requests.post('http://localhost:5000/ai-api/create-file',
    json={'file_path': 'new_feature.py', 'content': new_code})
```

### Searching Code
```python
response = requests.post('http://localhost:5000/ai-api/search-files',
    json={'search_term': 'ai_conversation', 'extensions': ['.py']})
```

## Integration with Existing Platform

The external AI integration seamlessly works with:
- 4-API conversation system (OpenAI, Anthropic, Gemini, Perplexity)
- Real-time conversation feeds
- Business dashboard management
- Social media automation
- Enterprise content ecosystem

## Security Considerations

- API endpoints require proper authentication in production
- File access is restricted to safe file types
- Automatic backup system prevents data loss
- All modifications are logged for audit trails

Generated by External AI - ''' + time.strftime('%Y-%m-%d %H:%M:%S')

        # Create documentation file
        result = self.create_file('EXTERNAL_AI_INTEGRATION.md', documentation)
        if result and result.get('success'):
            print("   ✅ Generated comprehensive documentation")
            
        return True
    
    def get_project_structure(self):
        """Get project structure via API"""
        try:
            response = requests.get(f"{self.ai_api_base}/project-structure", timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"   ❌ Error getting project structure: {e}")
            return None
    
    def read_file(self, file_path):
        """Read file content via API"""
        try:
            response = requests.post(f"{self.ai_api_base}/read-file", 
                                   json={'file_path': file_path}, timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"   ❌ Error reading {file_path}: {e}")
            return None
    
    def write_file(self, file_path, content):
        """Write file content via API"""
        try:
            response = requests.post(f"{self.ai_api_base}/write-file",
                                   json={'file_path': file_path, 'content': content, 'backup': True},
                                   timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"   ❌ Error writing {file_path}: {e}")
            return None
    
    def create_file(self, file_path, content):
        """Create new file via API"""
        try:
            response = requests.post(f"{self.ai_api_base}/create-file",
                                   json={'file_path': file_path, 'content': content},
                                   timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"   ❌ Error creating {file_path}: {e}")
            return None
    
    def search_files(self, search_term, extensions=None):
        """Search across project files"""
        try:
            payload = {'search_term': search_term}
            if extensions:
                payload['extensions'] = extensions
                
            response = requests.post(f"{self.ai_api_base}/search-files",
                                   json=payload, timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"   ❌ Error searching files: {e}")
            return None

def main():
    """Run the external AI demonstration"""
    print("🚀 Starting External AI Integration Demo")
    print("=" * 50)
    
    demo = ExternalAIDemo()
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        # Run demonstrations
        demo.demo_project_analysis()
        print("\n" + "=" * 50)
        
        demo.demo_code_enhancement()
        print("\n" + "=" * 50)
        
        demo.demo_documentation_generation()
        print("\n" + "=" * 50)
        
        print("✅ External AI Integration Demo Complete!")
        print("\n📝 Summary:")
        print("   - Project analyzed successfully")
        print("   - New AI features added")
        print("   - Documentation generated")
        print("   - API endpoints tested")
        print("\n🌐 Access the web interface at: http://localhost:5000/external-ai")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main()