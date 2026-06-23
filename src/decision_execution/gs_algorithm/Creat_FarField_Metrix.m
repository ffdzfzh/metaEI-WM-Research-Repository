function [metrix, metrix_inv] = Creat_FarField_Metrix(num_x, num_y, p, lambda, Theta_grid, Phi_grid)
    
    x_idx = (-num_x/2 : num_x/2 - 1) * p;
    y_idx = (-num_y/2 : num_y/2 - 1) * p;
    [X_elem, Y_elem] = meshgrid(x_idx, y_idx);
    
    X_vec = reshape(X_elem, [], 1);
    Y_vec = reshape(Y_elem, [], 1);
    
    Theta_rad = deg2rad(Theta_grid);
    Phi_rad = deg2rad(Phi_grid);
    
    % u = sin(theta)*cos(phi)
    % v = sin(theta)*sin(phi)
    % w = cos(theta)
    
    
    U_obs = sin(Theta_rad) .* cos(Phi_rad);
    V_obs = sin(Theta_rad) .* sin(Phi_rad);
    
    U_vec = reshape(U_obs, [], 1);
    V_vec = reshape(V_obs, [], 1);
    
    
    k = 2*pi/lambda;
    
    
    phase_term = k * (U_vec * X_vec.' + V_vec * Y_vec.');
    
    metrix = exp(1i * phase_term);
    
    metrix_inv = metrix'; 
end
