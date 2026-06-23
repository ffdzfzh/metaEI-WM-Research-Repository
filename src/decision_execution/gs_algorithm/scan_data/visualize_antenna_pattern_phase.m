clc
clear
close all

script_dir = fileparts(mfilename('fullpath'));
load(fullfile(script_dir, 'left_45deg_incidence_61p5cm.mat'))
% freq_index = 8;  % 8-3.5GHz
freq_index = 11;  % 11-5GHz
[ny, nx, nfreq] = size(Spara_matrix);
Es = Spara_matrix(:, :, freq_index);
% Es_amp = abs(Es);
% imagesc(Es_amp);
Es_angle = angle(Es);
imagesc(Es_angle);

% x_length = 640;
% y_length = 640;
% x_step = x_length / (nx-1);
% y_step = y_length / (ny-1);
% x_coords = linspace(0, x_length, nx);
% y_coords = linspace(0, y_length, ny);
% [X, Y] = meshgrid(x_coords, y_coords);
% 
% contourf(X, Y, Es_angle, 'LineColor', 'none');
colormap(parula(256));
colorbar;
xlabel('X', 'FontSize', 10);
ylabel('Y', 'FontSize', 10);
axis equal tight;
