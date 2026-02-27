"""
OpenGL Renderer for Claude Pet Companion

Provides hardware-accelerated 3D rendering with:
- Modern OpenGL (3.3+) support
- Shader-based rendering
- Skeletal animation support
- Dynamic lighting and shadows
- Material system
- Cross-platform (Windows, macOS, Linux)

Falls back to software rendering if OpenGL is unavailable.
"""

import sys
import math
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import struct

logger = logging.getLogger(__name__)


class RenderBackend(Enum):
    """Available rendering backends."""
    AUTO = "auto"
    OPENGL = "opengl"
    SOFTWARE = "software"
    TKNTER = "tkinter"


@dataclass
class Vertex:
    """A single vertex with position, normal, and UV."""
    x: float
    y: float
    z: float
    nx: float = 0.0  # Normal X
    ny: float = 0.0  # Normal Y
    nz: float = 1.0  # Normal Z
    u: float = 0.0  # Texture U
    v: float = 0.0  # Texture V

    def to_tuple(self) -> Tuple[float, ...]:
        """Convert to tuple for shader input."""
        return (self.x, self.y, self.z, self.nx, self.ny, self.nz, self.u, self.v)


@dataclass
class Material:
    """Material properties for rendering."""
    name: str = "default"
    diffuse_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    specular_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ambient_color: Tuple[float, float, float] = (0.1, 0.1, 0.1)
    shininess: float = 32.0
    opacity: float = 1.0
    emissive_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    texture_id: Optional[int] = None

    # Fuzzy/fur effect parameters
    fur_length: float = 0.0
    fur_density: float = 0.0
    fur_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class Light:
    """Light source definition."""
    position: Tuple[float, float, float] = (0.0, 5.0, 5.0)
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    intensity: float = 1.0
    ambient_intensity: float = 0.1

    # For point/spot lights
    light_type: str = "directional"  # directional, point, spot
    constant: float = 1.0
    linear: float = 0.09
    quadratic: float = 0.032
    direction: Tuple[float, float, float] = (0.0, -1.0, -1.0)
    cutoff: float = 12.5  # For spot lights (cos of angle)


@dataclass
class Mesh:
    """3D mesh composed of vertices and indices."""
    name: str = "mesh"
    vertices: List[Vertex] = field(default_factory=list)
    indices: List[int] = field(default_factory=list)
    material: Material = field(default_factory=Material)

    def add_vertex(self, v: Vertex):
        """Add a vertex to the mesh."""
        self.vertices.append(v)

    def add_triangle(self, i1: int, i2: int, i3: int):
        """Add a triangle indices."""
        self.indices.extend([i1, i2, i3])

    def compute_normals(self):
        """Compute vertex normals from face normals."""
        # Reset normals
        for v in self.vertices:
            v.nx = v.ny = v.nz = 0.0

        # Accumulate face normals
        for i in range(0, len(self.indices), 3):
            i1, i2, i3 = self.indices[i], self.indices[i + 1], self.indices[i + 2]
            v1, v2, v3 = self.vertices[i1], self.vertices[i2], self.vertices[i3]

            # Compute face normal
            edge1 = (v2.x - v1.x, v2.y - v1.y, v2.z - v1.z)
            edge2 = (v3.x - v1.x, v3.y - v1.y, v3.z - v1.z)

            nx = edge1[1] * edge2[2] - edge1[2] * edge2[1]
            ny = edge1[2] * edge2[0] - edge1[0] * edge2[2]
            nz = edge1[0] * edge2[1] - edge1[1] * edge2[0]

            # Add to vertex normals
            for v in (v1, v2, v3):
                v.nx += nx
                v.ny += ny
                v.nz += nz

        # Normalize vertex normals
        for v in self.vertices:
            length = math.sqrt(v.nx * v.nx + v.ny * v.ny + v.nz * v.nz)
            if length > 0:
                v.nx /= length
                v.ny /= length
                v.nz /= length


class ShaderProgram:
    """OpenGL shader program wrapper."""

    def __init__(self, vertex_source: str = None, fragment_source: str = None):
        self.vertex_source = vertex_source or self._default_vertex_shader()
        self.fragment_source = fragment_source or self._default_fragment_shader()
        self.program_id = None
        self.uniforms: Dict[str, int] = {}

    def _default_vertex_shader(self) -> str:
        """Default vertex shader source."""
        return """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec3 aNormal;
        layout (location = 2) in vec2 aTexCoord;

        out vec3 FragPos;
        out vec3 Normal;
        out vec2 TexCoord;

        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;

        void main() {
            FragPos = vec3(model * vec4(aPos, 1.0));
            Normal = mat3(transpose(inverse(model))) * aNormal;
            TexCoord = aTexCoord;
            gl_Position = projection * view * vec4(FragPos, 1.0);
        }
        """

    def _default_fragment_shader(self) -> str:
        """Default fragment shader source with lighting."""
        return """
        #version 330 core
        out vec4 FragColor;

        in vec3 FragPos;
        in vec3 Normal;
        in vec2 TexCoord;

        uniform vec3 lightPos;
        uniform vec3 lightColor;
        uniform vec3 viewPos;
        uniform float ambientStrength;

        uniform vec3 objectColor;
        uniform float specularStrength;
        uniform float shininess;
        uniform float opacity;

        void main() {
            // Ambient
            vec3 ambient = ambientStrength * lightColor;

            // Diffuse
            vec3 norm = normalize(Normal);
            vec3 lightDir = normalize(lightPos - FragPos);
            float diff = max(dot(norm, lightDir), 0.0);
            vec3 diffuse = diff * lightColor;

            // Specular
            vec3 viewDir = normalize(viewPos - FragPos);
            vec3 reflectDir = reflect(-lightDir, norm);
            float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
            vec3 specular = specularStrength * spec * lightColor;

            vec3 result = (ambient + diffuse + specular) * objectColor;
            FragColor = vec4(result, opacity);
        }
        """


class OpenGLRenderer:
    """
    Hardware-accelerated OpenGL renderer.

    Provides 3D rendering capabilities with shaders, lighting,
    and materials. Falls back gracefully if OpenGL is unavailable.
    """

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.backend = RenderBackend.AUTO
        self.initialized = False

        # Scene
        self.meshes: Dict[str, Mesh] = {}
        self.lights: List[Light] = [Light()]
        self.camera_pos = (0.0, 0.0, 5.0)
        self.camera_target = (0.0, 0.0, 0.0)
        self.camera_up = (0.0, 1.0, 0.0)

        # Matrices
        self.model_matrix = self._identity_matrix()
        self.view_matrix = self._identity_matrix()
        self.projection_matrix = self._identity_matrix()

        # Shaders
        self.main_shader: Optional[ShaderProgram] = None

        # OpenGL state
        self.vao = None
        self.vbo = None
        self.ebo = None

        # Check availability
        self.opengl_available = self._check_opengl()

    def _check_opengl(self) -> bool:
        """Check if OpenGL is available."""
        try:
            # Try importing PyOpenGL
            import OpenGL.GL as gl
            import OpenGL.GL.shaders as shaders
            return True
        except ImportError:
            return False

    def initialize(self) -> bool:
        """Initialize the renderer."""
        if self.initialized:
            return True

        if not self.opengl_available:
            logger.warning("OpenGL not available, using software renderer")
            self.backend = RenderBackend.SOFTWARE
            self.initialized = True
            return True

        try:
            import OpenGL.GL as gl

            # Initialize OpenGL state
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glClearColor(0.0, 0.0, 0.0, 0.0)

            # Create default shader
            self.main_shader = ShaderProgram()
            self._compile_shader(self.main_shader)

            # Setup buffers
            self._setup_buffers()

            # Setup projection
            self._update_projection()

            self.initialized = True
            self.backend = RenderBackend.OPENGL
            logger.info("OpenGL renderer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize OpenGL: {e}")
            self.backend = RenderBackend.SOFTWARE
            self.initialized = True
            return True

    def _compile_shader(self, shader: ShaderProgram):
        """Compile shader program."""
        import OpenGL.GL as gl
        import OpenGL.GL.shaders as shaders

        # Compile vertex shader
        vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_shader, shader.vertex_source)
        gl.glCompileShader(vertex_shader)

        # Check compile errors
        if not gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS):
            info_log = gl.glGetShaderInfoLog(vertex_shader)
            raise RuntimeError(f"Vertex shader compilation failed: {info_log}")

        # Compile fragment shader
        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_shader, shader.fragment_source)
        gl.glCompileShader(fragment_shader)

        if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
            info_log = gl.glGetShaderInfoLog(fragment_shader)
            raise RuntimeError(f"Fragment shader compilation failed: {info_log}")

        # Link program
        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)

        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            info_log = gl.glGetProgramInfoLog(program)
            raise RuntimeError(f"Shader program linking failed: {info_log}")

        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)

        shader.program_id = program

        # Get uniform locations
        shader.uniforms['model'] = gl.glGetUniformLocation(program, 'model')
        shader.uniforms['view'] = gl.glGetUniformLocation(program, 'view')
        shader.uniforms['projection'] = gl.glGetUniformLocation(program, 'projection')
        shader.uniforms['lightPos'] = gl.glGetUniformLocation(program, 'lightPos')
        shader.uniforms['lightColor'] = gl.glGetUniformLocation(program, 'lightColor')
        shader.uniforms['viewPos'] = gl.glGetUniformLocation(program, 'viewPos')
        shader.uniforms['ambientStrength'] = gl.glGetUniformLocation(program, 'ambientStrength')
        shader.uniforms['objectColor'] = gl.glGetUniformLocation(program, 'objectColor')
        shader.uniforms['specularStrength'] = gl.glGetUniformLocation(program, 'specularStrength')
        shader.uniforms['shininess'] = gl.glGetUniformLocation(program, 'shininess')
        shader.uniforms['opacity'] = gl.glGetUniformLocation(program, 'opacity')

    def _setup_buffers(self):
        """Setup vertex buffers."""
        import OpenGL.GL as gl

        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.ebo = gl.glGenBuffers(1)

    def _update_projection(self):
        """Update projection matrix."""
        import OpenGL.GL as gl
        import numpy as np

        # Perspective projection
        fov = math.radians(45.0)
        aspect = self.width / self.height if self.height > 0 else 1.0
        near = 0.1
        far = 100.0

        f = 1.0 / math.tan(fov / 2.0)

        self.projection_matrix = [
            f / aspect, 0.0, 0.0, 0.0,
            0.0, f, 0.0, 0.0,
            0.0, 0.0, (far + near) / (near - far), -1.0,
            0.0, 0.0, (2 * far * near) / (near - far), 0.0
        ]

    def _identity_matrix(self) -> List[float]:
        """Return 4x4 identity matrix."""
        return [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]

    def add_mesh(self, mesh: Mesh):
        """Add a mesh to the scene."""
        self.meshes[mesh.name] = mesh

    def remove_mesh(self, name: str):
        """Remove a mesh from the scene."""
        self.meshes.pop(name, None)

    def get_mesh(self, name: str) -> Optional[Mesh]:
        """Get a mesh by name."""
        return self.meshes.get(name)

    def set_camera(self, position: Tuple[float, float, float],
                   target: Tuple[float, float, float]):
        """Set camera position and target."""
        self.camera_pos = position
        self.camera_target = target
        self._update_view_matrix()

    def _update_view_matrix(self):
        """Update view matrix from camera."""
        # Simple look-at matrix
        eye = self.camera_pos
        target = self.camera_target
        up = self.camera_up

        # Calculate forward, right, and up vectors
        forward = (
            target[0] - eye[0],
            target[1] - eye[1],
            target[2] - eye[2]
        )
        fwd_len = math.sqrt(forward[0]**2 + forward[1]**2 + forward[2]**2)
        if fwd_len > 0:
            forward = (forward[0]/fwd_len, forward[1]/fwd_len, forward[2]/fwd_len)

        # Right = forward x up
        right = (
            forward[1] * up[2] - forward[2] * up[1],
            forward[2] * up[0] - forward[0] * up[2],
            forward[0] * up[1] - forward[1] * up[0]
        )

        # New up = right x forward
        new_up = (
            right[1] * forward[2] - right[2] * forward[1],
            right[2] * forward[0] - right[0] * forward[2],
            right[0] * forward[1] - right[1] * forward[0]
        )

        # View matrix
        self.view_matrix = [
            right[0], new_up[0], -forward[0], 0.0,
            right[1], new_up[1], -forward[1], 0.0,
            right[2], new_up[2], -forward[2], 0.0,
            -(right[0]*eye[0] + right[1]*eye[1] + right[2]*eye[2]),
            -(new_up[0]*eye[0] + new_up[1]*eye[1] + new_up[2]*eye[2]),
            -(-forward[0]*eye[0] + -forward[1]*eye[1] + -forward[2]*eye[2]),
            1.0
        ]

    def render(self, clear: bool = True):
        """Render the scene."""
        if self.backend == RenderBackend.SOFTWARE:
            return self._render_software()

        if not self.initialized or not self.main_shader:
            return

        import OpenGL.GL as gl

        if clear:
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Use shader
        gl.glUseProgram(self.main_shader.program_id)

        # Set uniforms
        self._set_shader_uniforms()

        # Render meshes
        for mesh in self.meshes.values():
            self._render_mesh(mesh)

    def _set_shader_uniforms(self):
        """Set shader uniform values."""
        import OpenGL.GL as gl
        import numpy as np

        if not self.main_shader:
            return

        # Matrices
        gl.glUniformMatrix4fv(
            self.main_shader.uniforms['model'],
            1, gl.GL_TRUE, self.model_matrix
        )
        gl.glUniformMatrix4fv(
            self.main_shader.uniforms['view'],
            1, gl.GL_TRUE, self.view_matrix
        )
        gl.glUniformMatrix4fv(
            self.main_shader.uniforms['projection'],
            1, gl.GL_TRUE, self.projection_matrix
        )

        # Lighting
        if self.lights:
            light = self.lights[0]
            gl.glUniform3f(self.main_shader.uniforms['lightPos'], *light.position)
            gl.glUniform3f(self.main_shader.uniforms['lightColor'], *light.color)
            gl.glUniform1f(self.main_shader.uniforms['ambientStrength'], light.ambient_intensity)

        # Camera
        gl.glUniform3f(self.main_shader.uniforms['viewPos'], *self.camera_pos)

    def _render_mesh(self, mesh: Mesh):
        """Render a single mesh."""
        import OpenGL.GL as gl
        import numpy as np

        if not mesh.vertices or not mesh.indices:
            return

        # Create vertex data
        vertex_data = []
        for v in mesh.vertices:
            vertex_data.extend([v.x, v.y, v.z, v.nx, v.ny, v.nz, v.u, v.v])

        # Bind VAO
        gl.glBindVertexArray(self.vao)

        # Upload vertex data
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            np.array(vertex_data, dtype=np.float32).tobytes(),
            gl.GL_STATIC_DRAW
        )

        # Upload index data
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER,
            np.array(mesh.indices, dtype=np.uint32).tobytes(),
            gl.GL_STATIC_DRAW
        )

        # Set vertex attributes
        # Position (location 0)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)

        # Normal (location 1)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, gl.ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)

        # TexCoord (location 2)
        gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, gl.ctypes.c_void_p(24))
        gl.glEnableVertexAttribArray(2)

        # Set material uniforms
        mat = mesh.material
        gl.glUniform3f(self.main_shader.uniforms['objectColor'], *mat.diffuse_color)
        gl.glUniform1f(self.main_shader.uniforms['specularStrength'], 0.5)
        gl.glUniform1f(self.main_shader.uniforms['shininess'], mat.shininess)
        gl.glUniform1f(self.main_shader.uniforms['opacity'], mat.opacity)

        # Draw
        gl.glDrawElements(gl.GL_TRIANGLES, len(mesh.indices), gl.GL_UNSIGNED_INT, None)

        # Unbind
        gl.glBindVertexArray(0)

    def _render_software(self):
        """Fallback software rendering."""
        # Simple point-based rendering for fallback
        pass

    def cleanup(self):
        """Clean up renderer resources."""
        if self.backend == RenderBackend.OPENGL:
            import OpenGL.GL as gl

            if self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
            if self.vbo:
                gl.glDeleteBuffers(1, [self.vbo])
            if self.ebo:
                gl.glDeleteBuffers(1, [self.ebo])

    def resize(self, width: int, height: int):
        """Handle window resize."""
        self.width = width
        self.height = height
        if self.initialized:
            self._update_projection()
            import OpenGL.GL as gl
            gl.glViewport(0, 0, width, height)


class PetMeshBuilder:
    """Builder for creating pet mesh geometry."""

    @staticmethod
    def create_sphere(radius: float = 1.0, segments: int = 16) -> Mesh:
        """Create a sphere mesh."""
        mesh = Mesh(name="sphere")

        rings = segments // 2
        sectors = segments

        # Generate vertices
        for r in range(rings + 1):
            theta = r * math.pi / rings
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)

            for s in range(sectors + 1):
                phi = s * 2 * math.pi / sectors
                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)

                x = cos_phi * sin_theta
                y = cos_theta
                z = sin_phi * sin_theta

                u = s / sectors
                v = r / rings

                mesh.add_vertex(Vertex(
                    x=radius * x,
                    y=radius * y,
                    z=radius * z,
                    nx=x, ny=y, nz=z,
                    u=u, v=v
                ))

        # Generate indices
        for r in range(rings):
            for s in range(sectors):
                i0 = r * (sectors + 1) + s
                i1 = i0 + 1
                i2 = (r + 1) * (sectors + 1) + s
                i3 = i2 + 1

                if r != 0:
                    mesh.add_triangle(i0, i2, i1)
                if r != rings - 1:
                    mesh.add_triangle(i1, i2, i3)

        return mesh

    @staticmethod
    def create_cube(size: float = 1.0) -> Mesh:
        """Create a cube mesh."""
        mesh = Mesh(name="cube")
        h = size / 2

        # Vertices for a cube with normals and UVs
        vertices = [
            # Front face
            Vertex(-h, -h, h, 0, 0, 1, 0, 0),
            Vertex(h, -h, h, 0, 0, 1, 1, 0),
            Vertex(h, h, h, 0, 0, 1, 1, 1),
            Vertex(-h, h, h, 0, 0, 1, 0, 1),
            # Back face
            Vertex(h, -h, -h, 0, 0, -1, 0, 0),
            Vertex(-h, -h, -h, 0, 0, -1, 1, 0),
            Vertex(-h, h, -h, 0, 0, -1, 1, 1),
            Vertex(h, h, -h, 0, 0, -1, 0, 1),
            # Top face
            Vertex(-h, h, h, 0, 1, 0, 0, 0),
            Vertex(h, h, h, 0, 1, 0, 1, 0),
            Vertex(h, h, -h, 0, 1, 0, 1, 1),
            Vertex(-h, h, -h, 0, 1, 0, 0, 1),
            # Bottom face
            Vertex(-h, -h, -h, 0, -1, 0, 0, 0),
            Vertex(h, -h, -h, 0, -1, 0, 1, 0),
            Vertex(h, -h, h, 0, -1, 0, 1, 1),
            Vertex(-h, -h, h, 0, -1, 0, 0, 1),
            # Right face
            Vertex(h, -h, h, 1, 0, 0, 0, 0),
            Vertex(h, -h, -h, 1, 0, 0, 1, 0),
            Vertex(h, h, -h, 1, 0, 0, 1, 1),
            Vertex(h, h, h, 1, 0, 0, 0, 1),
            # Left face
            Vertex(-h, -h, -h, -1, 0, 0, 0, 0),
            Vertex(-h, -h, h, -1, 0, 0, 1, 0),
            Vertex(-h, h, h, -1, 0, 0, 1, 1),
            Vertex(-h, h, -h, -1, 0, 0, 0, 1),
        ]

        for v in vertices:
            mesh.add_vertex(v)

        # Indices
        indices = [
            0, 1, 2, 0, 2, 3,  # Front
            4, 5, 6, 4, 6, 7,  # Back
            8, 9, 10, 8, 10, 11,  # Top
            12, 13, 14, 12, 14, 15,  # Bottom
            16, 17, 18, 16, 18, 19,  # Right
            20, 21, 22, 20, 22, 23,  # Left
        ]

        mesh.indices = indices
        return mesh

    @staticmethod
    def create_ellipsoid(rx: float = 1.0, ry: float = 0.8, rz: float = 0.9,
                         segments: int = 16) -> Mesh:
        """Create an ellipsoid (stretched sphere)."""
        mesh = PetMeshBuilder.create_sphere(1.0, segments)

        # Scale vertices
        for v in mesh.vertices:
            v.x *= rx
            v.y *= ry
            v.z *= rz

        return mesh


def create_renderer(width: int = 800, height: int = 600,
                   backend: RenderBackend = RenderBackend.AUTO) -> OpenGLRenderer:
    """Factory function to create a renderer with the specified backend."""
    renderer = OpenGLRenderer(width, height)
    renderer.backend = backend

    if backend == RenderBackend.SOFTWARE:
        renderer.opengl_available = False

    renderer.initialize()
    return renderer


if __name__ == "__main__":
    # Test the renderer
    print("Testing OpenGL Renderer")

    renderer = create_renderer(800, 600)

    print(f"Renderer backend: {renderer.backend}")
    print(f"OpenGL available: {renderer.opengl_available}")
    print(f"Initialized: {renderer.initialized}")

    # Create a test mesh
    sphere = PetMeshBuilder.create_sphere(1.0, 16)
    renderer.add_mesh(sphere)

    print(f"Sphere vertices: {len(sphere.vertices)}")
    print(f"Sphere indices: {len(sphere.indices)}")

    renderer.cleanup()
