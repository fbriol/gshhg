"""This script is the entry point for building, distributing and installing
this module using distutils/setuptools."""
import os
import pathlib
import platform
import sys
import sysconfig

import packaging.version
import setuptools
import setuptools.command.build_ext

# Check Python requirement
MAJOR = sys.version_info[0]
MINOR = sys.version_info[1]
if not (MAJOR >= 3 and MINOR >= 6):
    raise RuntimeError('Python %d.%d is not supported, '
                       'you need at least Python 3.6.' % (MAJOR, MINOR))

# Working directory
WORKING_DIRECTORY = pathlib.Path(__file__).parent.absolute()


def distutils_dirname(prefix=None, extname=None) -> pathlib.Path:
    """Returns the name of the build directory."""
    prefix = 'lib' or prefix
    extname = '' if extname is None else os.sep.join(extname.split('.')[:-1])
    if packaging.version.parse(
            setuptools.__version__) >= packaging.version.parse('62.1'):
        return pathlib.Path(
            WORKING_DIRECTORY, 'build', f'{prefix}.{sysconfig.get_platform()}-'
            f'{sys.implementation.cache_tag}', extname)
    return pathlib.Path(
        WORKING_DIRECTORY, 'build', f'{prefix}.{sysconfig.get_platform()}-'
        f'{sys.version_info[0]}.{sys.version_info[1]}', extname)


class CMakeExtension(setuptools.Extension):
    """Python extension to build."""

    def __init__(self, name):
        super().__init__(name, sources=[])


class BuildExt(setuptools.command.build_ext.build_ext):
    """Build the Python extension using cmake."""

    user_options = setuptools.command.build_ext.build_ext.user_options
    user_options += [
        ('boost-root=', None, 'Preferred Boost installation prefix'),
        ('cxx-compiler=', None, 'Preferred C++ compiler'),
        ('reconfigure', None, 'Forces CMake to reconfigure this project')
    ]

    def initialize_options(self) -> None:
        """Set default values for all the options that this command
        supports."""
        super().initialize_options()
        self.boost_root = None
        self.conda_forge = None
        self.cxx_compiler = None
        self.reconfigure = None

    def run(self):
        """Run the command."""
        for ext in self.extensions:
            self.build_cmake(ext)
        super().run()

    @staticmethod
    def is_conda():
        """Detect if the Python interpreter is part of a conda distribution."""
        result = pathlib.Path(sys.prefix, 'conda-meta').exists()
        if not result:
            try:
                # pylint: disable=unused-import
                import conda  # noqa: F401

                # pylint: enable=unused-import
            except ImportError:
                result = False
            else:
                result = True
        return result

    @staticmethod
    def boost():
        """Get the default boost path in Anaconda's environment."""
        # Do not search system for Boost & disable the search for boost-cmake
        boost_option = '-DBoost_NO_SYSTEM_PATHS=TRUE ' \
            '-DBoost_NO_BOOST_CMAKE=TRUE'
        boost_root = sys.prefix
        if pathlib.Path(boost_root, 'include', 'boost').exists():
            return '{boost_option} -DBOOST_ROOT={boost_root}'.format(
                boost_root=boost_root, boost_option=boost_option).split()
        boost_root = pathlib.Path(sys.prefix, 'Library', 'include')
        if not boost_root.exists():
            raise RuntimeError(
                'Unable to find the Boost library in the conda distribution '
                'used.')
        return '{boost_option} -DBoost_INCLUDE_DIR={boost_root}'.format(
            boost_root=boost_root, boost_option=boost_option).split()

    def set_cmake_user_options(self):
        """Sets the options defined by the user."""
        is_conda = self.is_conda()
        result = []

        if self.cxx_compiler is not None:
            result.append('-DCMAKE_CXX_COMPILER=' + self.cxx_compiler)

        if self.boost_root is not None:
            result.append('-DBOOSTROOT=' + self.boost_root)
        elif is_conda:
            cmake_variable = self.boost()
            if cmake_variable:
                result += cmake_variable

        return result

    def build_cmake(self, ext):
        """Execute cmake to build the Python extension."""
        # These dirs will be created in build_py, so if you don't have
        # any python sources to bundle, the dirs will be missing
        build_temp = pathlib.Path(WORKING_DIRECTORY, self.build_temp)
        build_temp.mkdir(parents=True, exist_ok=True)
        extdir = str(
            pathlib.Path(self.get_ext_fullpath(ext.name)).parent.resolve())

        cfg = 'Debug' if self.debug else 'Release'

        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + str(extdir),
            '-DPYTHON_EXECUTABLE=' + sys.executable,
            '-DCMAKE_PREFIX_PATH=' + sys.prefix
        ] + self.set_cmake_user_options()

        build_args = ['--config', cfg]

        if platform.system() != 'Windows':
            build_args += ['--', '-j%d' % os.cpu_count()]
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            if platform.system() == 'Darwin':
                cmake_args += ['-DCMAKE_OSX_DEPLOYMENT_TARGET=10.15']
        else:
            cmake_args += [
                '-G', 'Visual Studio 15 2017',
                '-DCMAKE_GENERATOR_PLATFORM=x64',
                '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(
                    cfg.upper(), extdir)
            ]
            build_args += ['--', '/m']
            if self.verbose:
                build_args += ['/verbosity:n']

        if self.verbose:
            build_args.insert(0, '--verbose')

        os.chdir(str(build_temp))

        # Has CMake ever been executed?
        if pathlib.Path(build_temp, 'CMakeFiles',
                        'TargetDirectories.txt').exists():
            # The user must force the reconfiguration
            configure = self.reconfigure is not None
        else:
            configure = True

        if configure:
            self.spawn(['cmake', str(WORKING_DIRECTORY)] + cmake_args)
        if not self.dry_run:
            self.spawn(['cmake', '--build', '.', '--target', 'core'] +
                       build_args)
        os.chdir(str(WORKING_DIRECTORY))


def main():
    setuptools.setup(
        name='gshhg',
        # version=revision(),
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Topic :: Scientific/Engineering :: Physics',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English', 'Operating System :: POSIX',
            'Operating System :: MacOS',
            'Operating System :: Microsoft :: Windows',
            'Programming Language :: Python :: 3.8'
            'Programming Language :: Python :: 3.9'
            'Programming Language :: Python :: 3.10'
            'Programming Language :: Python :: 3.11'
        ],
        description='TODO',
        url='TODO',
        author='CNES/CLS',
        license='BSD License',
        ext_modules=[CMakeExtension(name='gshhg.core')],
        setup_requires=['pybind11'],
        install_requires=['numpy', 'dask', 'xarray'],
        tests_require=['numpy', 'dask', 'xarray'],
        package_dir={'': 'src'},
        packages=setuptools.find_packages(where='src'),
        cmdclass={'build_ext': BuildExt},
        zip_safe=False)


if __name__ == '__main__':
    main()
