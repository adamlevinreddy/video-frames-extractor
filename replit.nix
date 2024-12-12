
{ pkgs }: {
  deps = [
    pkgs.python312
    pkgs.python312Packages.opencv4
    pkgs.python312Packages.flask
    pkgs.python312Packages.imutils
    pkgs.python312Packages.fire
    pkgs.libGLU
    pkgs.libGL
  ];
}
