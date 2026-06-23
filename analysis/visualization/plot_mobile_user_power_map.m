clc;
clear;
close all;

script_dir = fileparts(mfilename('fullpath'));
repo_root = fileparts(fileparts(script_dir));
json_with_ris = fullfile(repo_root, 'data', 'power_maps', 'scene1_point1.json');
step_size = 0.5;
map_down = -60;

x_obs_min = -inf; 
x_obs_max = inf;  
y_obs_min = -inf; 
y_obs_max = inf;  

disp('Reading JSON data...');
data_with = jsondecode(fileread(json_with_ris));

x_with_all = [data_with.x]'; 
y_with_all = [data_with.y]'; 
p_with_all = [data_with.power]';

disp('Reconstructing the power grid...');
valid_idx = (x_with_all >= x_obs_min) & (x_with_all <= x_obs_max) & ...
            (y_with_all >= y_obs_min) & (y_with_all <= y_obs_max);

x_with = x_with_all(valid_idx);
y_with = y_with_all(valid_idx);
p_with = p_with_all(valid_idx);

if isempty(x_with)
    error('No samples fall inside the selected observation region.');
end

X_vec = min(x_with) : step_size : max(x_with);
Y_vec = min(y_with) : step_size : max(y_with);
[Xg, Yg] = meshgrid(X_vec, Y_vec);

P_map_with_ris = nan(size(Xg));

for i = 1:length(x_with)
    c = round((x_with(i) - X_vec(1)) / step_size) + 1;
    r = round((y_with(i) - Y_vec(1)) / step_size) + 1;
    P_map_with_ris(r, c) = p_with(i);
end

disp('Rendering the top-view power map...');
fig1 = figure('Name', '2D Top View Power Map', 'Color', 'w', 'Position', [100, 100, 800, 600]);
hold on; axis equal tight; axis off;

view(180, 90); 

Z_flat = zeros(size(Xg));
surf(Xg, Yg, Z_flat, P_map_with_ris, 'EdgeColor', 'none', 'FaceAlpha', 0.85);
shading interp; colormap('jet'); clim([map_down -10]); 

set(gca, 'Position', [0 0 1 1]);
camzoom(1);

% set(fig1, 'PaperUnits', 'inches', 'PaperPosition', [0 0 12 9]);
% print(fig1, 'picture_show/scene1_power_point1.png', '-dpng', '-r300');

disp('Plot complete.');
